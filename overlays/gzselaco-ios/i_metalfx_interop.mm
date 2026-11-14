#include "i_metalfx_interop.h"
#include "i_metalfx_event_validation.h"
#include <cstdio>
extern "C" void SelacoIOSReportLicensedAssetProbe(const char*,const char*);
#if !__has_feature(objc_arc)
#error i_metalfx_interop.mm requires ARC
#endif
struct IOSMetalFXInterop {
    IOSMetalFXInteropConfig config;
    id<MTLDevice> device;
    id<MTLCommandQueue> vulkanQueue;
    id<MTLSharedEvent> sceneReady, metalDone;
    id<MTLCommandBuffer> pending;
    uint64_t lastWait = 0, lastSignal = 0;
};
static bool CommandIsOpen(id<MTLCommandBuffer> cb, id<MTLDevice> device) {
    return cb && cb.device == device && cb.status <= MTLCommandBufferStatusEnqueued;
}
IOSMetalFXInteropStatus IOSMetalFXInteropCreate(const IOSMetalFXInteropConfig& c, IOSMetalFXInterop** out) {
    if (!out) return IOSMetalFXInteropStatus::InvalidArgument;
    *out = nullptr;
    if (!c.device || !c.vulkanQueue || !c.sceneReady || !c.metalDone || c.sceneReady == c.metalDone)
        return IOSMetalFXInteropStatus::InvalidArgument;
    if (!c.metalObjectsEnabled || !c.timelineSemaphoreEnabled || !c.exportMetalObjects ||
        !c.deviceExportDeclaredAtInstanceCreate || !c.queueExportDeclaredAtInstanceCreate ||
        !c.semaphoreExportsDeclaredAtCreate ||
        c.sceneReadyType != VK_SEMAPHORE_TYPE_TIMELINE || c.metalDoneType != VK_SEMAPHORE_TYPE_TIMELINE)
        return IOSMetalFXInteropStatus::Unsupported;
    VkExportMetalSharedEventInfoEXT done{};
    done.sType = VK_STRUCTURE_TYPE_EXPORT_METAL_SHARED_EVENT_INFO_EXT;
    done.semaphore = c.metalDone;
    VkExportMetalSharedEventInfoEXT ready{};
    ready.sType = VK_STRUCTURE_TYPE_EXPORT_METAL_SHARED_EVENT_INFO_EXT;
    ready.semaphore = c.sceneReady; ready.pNext = &done;
    VkExportMetalCommandQueueInfoEXT queue{};
    queue.sType = VK_STRUCTURE_TYPE_EXPORT_METAL_COMMAND_QUEUE_INFO_EXT;
    queue.queue = c.vulkanQueue; queue.pNext = &ready;
    VkExportMetalDeviceInfoEXT dev{};
    dev.sType = VK_STRUCTURE_TYPE_EXPORT_METAL_DEVICE_INFO_EXT; dev.pNext = &queue;
    VkExportMetalObjectsInfoEXT exports{};
    exports.sType = VK_STRUCTURE_TYPE_EXPORT_METAL_OBJECTS_INFO_EXT; exports.pNext = &dev;
    c.exportMetalObjects(c.device, &exports);
    // One bounded receipt: flags only, no pointers or private device identifiers.
    static bool exportReported=false;
    if(!exportReported){
        exportReported=true;char receipt[256];
        std::snprintf(receipt,sizeof(receipt),"device=%d queue=%d queueMatches=%d ready=%d done=%d distinct=%d readyUnbound=%d doneUnbound=%d",
            dev.mtlDevice!=nil,queue.mtlCommandQueue!=nil,queue.mtlCommandQueue.device==dev.mtlDevice,
            ready.mtlSharedEvent!=nil,done.mtlSharedEvent!=nil,ready.mtlSharedEvent!=done.mtlSharedEvent,
            ready.mtlSharedEvent.device==nil,done.mtlSharedEvent.device==nil);
        SelacoIOSReportLicensedAssetProbe("metalfx_export_flags",receipt);
    }
    if (!IOSMetalFXExportObjectsValid((__bridge const void*)dev.mtlDevice,
        (__bridge const void*)queue.mtlCommandQueue, (__bridge const void*)queue.mtlCommandQueue.device,
        (__bridge const void*)ready.mtlSharedEvent, (__bridge const void*)done.mtlSharedEvent,
        (__bridge const void*)ready.mtlSharedEvent.device, (__bridge const void*)done.mtlSharedEvent.device))
        return IOSMetalFXInteropStatus::ExportFailed;
    auto* p = new IOSMetalFXInterop{};
    p->config = c; p->device = dev.mtlDevice; p->vulkanQueue = queue.mtlCommandQueue;
    p->sceneReady = ready.mtlSharedEvent; p->metalDone = done.mtlSharedEvent;
    p->lastWait = c.lastSceneReadyValue; p->lastSignal = c.lastMetalDoneValue;
    *out = p; return IOSMetalFXInteropStatus::Ready;
}
void IOSMetalFXInteropDestroy(IOSMetalFXInterop* p) { delete p; }
id<MTLDevice> IOSMetalFXInteropDevice(const IOSMetalFXInterop* p) { return p ? p->device : nil; }
IOSMetalFXInteropStatus IOSMetalFXInteropTexture(IOSMetalFXInterop* p, const IOSMetalFXExportImage& i, id<MTLTexture>* out) {
    if (!out) return IOSMetalFXInteropStatus::InvalidArgument;
    *out = nil;
    if (!p || bool(i.image) == bool(i.imageView) || !i.textureExportDeclaredAtCreate)
        return IOSMetalFXInteropStatus::InvalidArgument;
    // This bridge deliberately excludes multiplanar/YUV images and stencil views.
    if (i.plane != VK_IMAGE_ASPECT_COLOR_BIT && i.plane != VK_IMAGE_ASPECT_DEPTH_BIT)
        return IOSMetalFXInteropStatus::InvalidArgument;
    VkExportMetalTextureInfoEXT texture{};
    texture.sType = VK_STRUCTURE_TYPE_EXPORT_METAL_TEXTURE_INFO_EXT;
    texture.image = i.image; texture.imageView = i.imageView; texture.plane = i.plane;
    VkExportMetalObjectsInfoEXT exports{};
    exports.sType = VK_STRUCTURE_TYPE_EXPORT_METAL_OBJECTS_INFO_EXT; exports.pNext = &texture;
    p->config.exportMetalObjects(p->config.device, &exports);
    id<MTLTexture> t = texture.mtlTexture;
    if (!t || t.device != p->device || t.textureType != MTLTextureType2D ||
        t.sampleCount != 1 || t.storageMode == MTLStorageModeMemoryless)
        return IOSMetalFXInteropStatus::ExportFailed;
    *out = t; return IOSMetalFXInteropStatus::Ready;
}
IOSMetalFXInteropStatus IOSMetalFXInteropBegin(IOSMetalFXInterop* p, id<MTLCommandBuffer> cb, uint64_t value) {
    if (!p || !CommandIsOpen(cb,p->device) || cb.commandQueue == p->vulkanQueue || value == 0) return IOSMetalFXInteropStatus::InvalidArgument;
    if (p->pending || value <= p->lastWait) return IOSMetalFXInteropStatus::InvalidSequence;
    [cb encodeWaitForEvent:p->sceneReady value:value];
    p->pending = cb; p->lastWait = value;
    return IOSMetalFXInteropStatus::Encoded;
}
IOSMetalFXInteropStatus IOSMetalFXInteropEnd(IOSMetalFXInterop* p, id<MTLCommandBuffer> cb, uint64_t value) {
    if (!p || !CommandIsOpen(cb,p->device) || cb.commandQueue == p->vulkanQueue || value == 0) return IOSMetalFXInteropStatus::InvalidArgument;
    if (p->pending != cb || value <= p->lastSignal) return IOSMetalFXInteropStatus::InvalidSequence;
    [cb encodeSignalEvent:p->metalDone value:value];
    p->pending = nil; p->lastSignal = value;
    return IOSMetalFXInteropStatus::Encoded;
}

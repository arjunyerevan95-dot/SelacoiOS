#include "i_metalfx_backend.h"
#include "i_metalfx_bridge.h"
#include "i_metalfx_interop.h"
#include <zvulkan/vulkandevice.h>
#include <zvulkan/vulkanobjects.h>
#include <atomic>
#include <memory>
#include <cstdlib>
#include <cstring>
#include <cstdio>
#include "engineerrors.h"
#if !__has_feature(objc_arc)
#error MetalFX backend requires ARC
#endif
// Vulkan owns final output/presentation. This separate queue never owns a drawable.
struct IOSMetalFXBackend {
    VulkanDevice* vk=nullptr;
    VkSemaphore ready=VK_NULL_HANDLE,done=VK_NULL_HANDLE;
    uint64_t value=0;
    bool recreate=false;
    IOSMetalFXInterop* interop=nullptr;
    IOSMetalFXBridge* bridge=nullptr;
    id<MTLCommandQueue> queue;
    id<MTLComputePipelineState> crop;
    id<MTLTexture> color,depth,motion;
    uint32_t width=0,height=0,outWidth=0,outHeight=0;
    // Keep completion-handler storage alive without capturing the C++ owner.
    std::shared_ptr<std::atomic<bool>> failed=std::make_shared<std::atomic<bool>>(false);
    ~IOSMetalFXBackend() {
        IOSMetalFXDestroy(bridge); IOSMetalFXInteropDestroy(interop);
        if(ready) vkDestroySemaphore(vk->device,ready,nullptr);
        if(done) vkDestroySemaphore(vk->device,done,nullptr);
    }
};
static bool Timeline(VulkanDevice* d,VkSemaphore* out) {
    VkExportMetalObjectCreateInfoEXT e{};e.sType=VK_STRUCTURE_TYPE_EXPORT_METAL_OBJECT_CREATE_INFO_EXT;
    e.exportObjectType=VK_EXPORT_METAL_OBJECT_TYPE_METAL_SHARED_EVENT_BIT_EXT;
    VkSemaphoreTypeCreateInfo t{};t.sType=VK_STRUCTURE_TYPE_SEMAPHORE_TYPE_CREATE_INFO;
    t.semaphoreType=VK_SEMAPHORE_TYPE_TIMELINE;t.pNext=&e;
    VkSemaphoreCreateInfo c{};c.sType=VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO;c.pNext=&t;
    return vkCreateSemaphore(d->device,&c,nullptr,out)==VK_SUCCESS;
}
static id<MTLTexture> Texture(id<MTLDevice>d,uint32_t w,uint32_t h,MTLPixelFormat f,MTLTextureUsage u){
    auto td=[MTLTextureDescriptor texture2DDescriptorWithPixelFormat:f width:w height:h mipmapped:NO];
    td.storageMode=MTLStorageModePrivate;td.usage=u|MTLTextureUsageShaderRead|MTLTextureUsageShaderWrite;
    return [d newTextureWithDescriptor:td];
}
static IOSMetalFXBackend* Create(VulkanDevice*d,const IOSMetalFXVkFrame&f){
    if(!d->Instance->EnabledExtensions.count(VK_EXT_METAL_OBJECTS_EXTENSION_NAME)||
       !d->EnabledFeatures.TimelineSemaphore.timelineSemaphore)return nullptr;
    auto p=std::make_unique<IOSMetalFXBackend>();p->vk=d;
    if(!Timeline(d,&p->ready)||!Timeline(d,&p->done))return nullptr;
    IOSMetalFXInteropConfig c{};c.device=d->device;c.vulkanQueue=d->GraphicsQueue;
    c.exportMetalObjects=(PFN_vkExportMetalObjectsEXT)vkGetInstanceProcAddr(d->Instance->Instance,"vkExportMetalObjectsEXT");
    c.sceneReady=p->ready;c.metalDone=p->done;c.metalObjectsEnabled=true;c.timelineSemaphoreEnabled=true;
    c.deviceExportDeclaredAtInstanceCreate=true;c.queueExportDeclaredAtInstanceCreate=true;c.semaphoreExportsDeclaredAtCreate=true;
    c.sceneReadyType=c.metalDoneType=VK_SEMAPHORE_TYPE_TIMELINE;
    if(IOSMetalFXInteropCreate(c,&p->interop)!=IOSMetalFXInteropStatus::Ready)return nullptr;
    id<MTLDevice> device=IOSMetalFXInteropDevice(p->interop);p->queue=[device newCommandQueue];
    p->queue.label=@"Selaco MetalFX interop";
    IOSMetalFXConfig cfg{};cfg.inputWidth=f.width;cfg.inputHeight=f.height;
    cfg.outputWidth=f.outputWidth;cfg.outputHeight=f.outputHeight;
    cfg.colorFormat=cfg.outputFormat=MTLPixelFormatRGBA16Float;
    cfg.depthFormat=MTLPixelFormatR32Float;cfg.motionFormat=MTLPixelFormatRG16Float;
    cfg.frameInterpolation=false;cfg.autoExposure=true;
    if(IOSMetalFXCreate(device,cfg,&p->bridge)!=IOSMetalFXStatus::Ready)return nullptr;
    auto u=IOSMetalFXGetUsage(p->bridge);
    p->color=Texture(device,f.width,f.height,cfg.colorFormat,u.color);
    p->depth=Texture(device,f.width,f.height,cfg.depthFormat,u.depth);
    p->motion=Texture(device,f.width,f.height,cfg.motionFormat,u.motion);
    // Exact low-resolution input textures, including depth-only conversion.
    NSString* source=@"#include <metal_stdlib>\nusing namespace metal;\n"
    "kernel void crop(texture2d<float,access::read> c[[texture(0)]],depth2d<float,access::read> d[[texture(1)]],"
    "texture2d<float,access::read> m[[texture(2)]],texture2d<float,access::write> co[[texture(3)]],"
    "texture2d<float,access::write> de[[texture(4)]],texture2d<float,access::write> mo[[texture(5)]],"
    "constant uint2& origin[[buffer(0)]],uint2 p[[thread_position_in_grid]]){"
    "if(p.x>=co.get_width()||p.y>=co.get_height())return;uint2 q=p+origin;"
    "co.write(c.read(q),p);de.write(float4(d.read(q),0,0,1),p);mo.write(m.read(q),p);}";
    NSError* error=nil;id<MTLLibrary> lib=[device newLibraryWithSource:source options:nil error:&error];
    if(lib)p->crop=[device newComputePipelineStateWithFunction:[lib newFunctionWithName:@"crop"] error:&error];
    if(!p->queue||!p->crop||!p->color||!p->depth||!p->motion)return nullptr;
    p->width=f.width;p->height=f.height;p->outWidth=f.outputWidth;p->outHeight=f.outputHeight;
    return p.release();
}
static bool Submit(VulkanDevice*d,VkSemaphore semaphore,uint64_t value,bool signal){
    VkTimelineSemaphoreSubmitInfo t{};t.sType=VK_STRUCTURE_TYPE_TIMELINE_SEMAPHORE_SUBMIT_INFO;
    VkSubmitInfo s{};s.sType=VK_STRUCTURE_TYPE_SUBMIT_INFO;s.pNext=&t;
    VkPipelineStageFlags stage=VK_PIPELINE_STAGE_ALL_COMMANDS_BIT;
    if(signal){t.signalSemaphoreValueCount=1;t.pSignalSemaphoreValues=&value;s.signalSemaphoreCount=1;s.pSignalSemaphores=&semaphore;}
    else{t.waitSemaphoreValueCount=1;t.pWaitSemaphoreValues=&value;s.waitSemaphoreCount=1;s.pWaitSemaphores=&semaphore;s.pWaitDstStageMask=&stage;}
    return vkQueueSubmit(d->GraphicsQueue,1,&s,VK_NULL_HANDLE)==VK_SUCCESS;
}
bool IOSMetalFXBackendConsume(IOSMetalFXBackend*&p,VulkanDevice*d,const IOSMetalFXVkFrame&f){
    const char* opt=std::getenv("SELACO_IOS_METALFX");
    if(!opt||std::strcmp(opt,"1")||!f.completeMotion||!d||!f.flushProducer||!f.width||!f.height||
       !f.outputWidth||!f.outputHeight||!f.color||!f.depth||!f.motion||!f.output)return false;
    if(!p)p=Create(d,f);
    if(!p||p->vk!=d||p->failed->load())return false;
    if(p->width!=f.width||p->height!=f.height||p->outWidth!=f.outputWidth||p->outHeight!=f.outputHeight){p->recreate=true;return false;}
    id<MTLTexture> color=nil,depth=nil,motion=nil,output=nil;
    IOSMetalFXExportImage e{};e.textureExportDeclaredAtCreate=true;e.image=f.color;
    if(IOSMetalFXInteropTexture(p->interop,e,&color)!=IOSMetalFXInteropStatus::Ready)return false;
    e.image=VK_NULL_HANDLE;e.imageView=f.depth;e.plane=VK_IMAGE_ASPECT_DEPTH_BIT;
    if(IOSMetalFXInteropTexture(p->interop,e,&depth)!=IOSMetalFXInteropStatus::Ready)return false;
    e.imageView=VK_NULL_HANDLE;e.image=f.motion;e.plane=VK_IMAGE_ASPECT_COLOR_BIT;
    if(IOSMetalFXInteropTexture(p->interop,e,&motion)!=IOSMetalFXInteropStatus::Ready)return false;
    e.image=f.output;if(IOSMetalFXInteropTexture(p->interop,e,&output)!=IOSMetalFXInteropStatus::Ready)return false;
    if(uint64_t(f.x)+f.width>color.width||uint64_t(f.y)+f.height>color.height||
       uint64_t(f.x)+f.width>depth.width||uint64_t(f.y)+f.height>depth.height||
       uint64_t(f.x)+f.width>motion.width||uint64_t(f.y)+f.height>motion.height)return false;
    auto usage=IOSMetalFXGetUsage(p->bridge);
    if(output.width!=f.outputWidth||output.height!=f.outputHeight||output.pixelFormat!=MTLPixelFormatRGBA16Float||
       (output.usage&usage.output)!=usage.output)return false;
    if(p->value==UINT64_MAX)return false;
    const uint64_t value=++p->value;
    id<MTLCommandBuffer> cb=[p->queue commandBuffer];cb.label=@"Selaco temporal upscale";
    if(IOSMetalFXInteropBegin(p->interop,cb,value)!=IOSMetalFXInteropStatus::Encoded)return false;
    auto enc=[cb computeCommandEncoder];
    if(!enc){p->failed->store(true);return false;}
    [enc setComputePipelineState:p->crop];
    [enc setTexture:color atIndex:0];[enc setTexture:depth atIndex:1];[enc setTexture:motion atIndex:2];
    [enc setTexture:p->color atIndex:3];[enc setTexture:p->depth atIndex:4];[enc setTexture:p->motion atIndex:5];
    uint32_t origin[2]={f.x,f.y};[enc setBytes:origin length:sizeof(origin) atIndex:0];
    [enc dispatchThreads:MTLSizeMake(f.width,f.height,1) threadsPerThreadgroup:MTLSizeMake(8,8,1)];[enc endEncoding];
    IOSMetalFXFrame temporal{};temporal.color=p->color;temporal.depth=p->depth;temporal.motion=p->motion;temporal.output=output;
    temporal.jitterX=f.jitterX;temporal.jitterY=f.jitterY;temporal.motionScaleX=float(f.width);temporal.motionScaleY=float(f.height);temporal.reset=f.reset;
    if(IOSMetalFXEncodeTemporal(p->bridge,cb,temporal)!=IOSMetalFXStatus::Encoded ||
       IOSMetalFXInteropEnd(p->interop,cb,value)!=IOSMetalFXInteropStatus::Encoded){p->failed->store(true);return false;}
    // All failure-prone encoding/preflight happened before submitting the producer.
    f.flushProducer(f.user);
    if(!Submit(d,p->ready,value,true)){p->failed->store(true);I_FatalError("MetalFX producer timeline submit failed; unsafe to continue rendering");}
    auto failed=p->failed;
    '[cb addCompletedHandler:^(id<MTLCommandBuffer> completed){
        if(completed.status==MTLCommandBufferStatusError){
            failed->store(true);
            // The GPU signal may not execute on error. Do not leave the Vulkan
            // consumer hanging, or host-signal it and present undefined pixels.
            // Termination is independent of the render thread blocked on fences.
            std::fputs("MetalFX GPU failure: terminating instead of waiting on an unsignalled timeline\\n",stderr);
            std::abort();
        }
    }];'
    [cb commit];
    // A failed Vulkan submit means device loss/error, not a valid fallback frame.
    if(!Submit(d,p->done,value,false)){p->failed->store(true);I_FatalError("MetalFX consumer timeline submit failed; unsafe to continue rendering");}
    return true;
}
void IOSMetalFXBackendDestroy(IOSMetalFXBackend*p){delete p;}

void IOSMetalFXBackendRetire(IOSMetalFXBackend*&p){if(p && (p->recreate||p->failed->load())){delete p;p=nullptr;}}

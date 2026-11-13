#pragma once
#ifdef __OBJC__
#import <Metal/Metal.h>
#include <vulkan/vulkan.h>
#include <vulkan/vulkan_metal.h>
#include <cstdint>
// Requires ARC. No Vulkan objects, queues, submissions or textures are created.
// Single-thread ownership. Vulkan handles must outlive this interop and all GPU work.
enum class IOSMetalFXInteropStatus { Ready, Encoded, InvalidArgument, Unsupported, ExportFailed, InvalidSequence };
struct IOSMetalFXInteropConfig {
    VkDevice device = VK_NULL_HANDLE;
    VkQueue vulkanQueue = VK_NULL_HANDLE;
    PFN_vkExportMetalObjectsEXT exportMetalObjects = nullptr;
    VkSemaphore sceneReady = VK_NULL_HANDLE;
    VkSemaphore metalDone = VK_NULL_HANDLE;
    // Caller must pass actual creation state, not mere extension availability.
    bool metalObjectsEnabled = false;
    bool timelineSemaphoreEnabled = false;
    bool deviceExportDeclaredAtInstanceCreate = false;
    bool queueExportDeclaredAtInstanceCreate = false;
    bool semaphoreExportsDeclaredAtCreate = false;
    VkSemaphoreType sceneReadyType = VK_SEMAPHORE_TYPE_BINARY;
    VkSemaphoreType metalDoneType = VK_SEMAPHORE_TYPE_BINARY;
    // Highest previously reserved/signalled values, including in-flight work.
    uint64_t lastSceneReadyValue = 0;
    uint64_t lastMetalDoneValue = 0;
};
struct IOSMetalFXExportImage {
    // Exactly one of image/imageView. Both must originate from the configured device.
    VkImage image = VK_NULL_HANDLE;
    VkImageView imageView = VK_NULL_HANDLE;
    VkImageAspectFlagBits plane = VK_IMAGE_ASPECT_COLOR_BIT;
    bool textureExportDeclaredAtCreate = false;
};
struct IOSMetalFXInterop;
IOSMetalFXInteropStatus IOSMetalFXInteropCreate(const IOSMetalFXInteropConfig&, IOSMetalFXInterop**);
// Only destroy after caller has retired GPU work; this function never waits.
void IOSMetalFXInteropDestroy(IOSMetalFXInterop*);
id<MTLDevice> IOSMetalFXInteropDevice(const IOSMetalFXInterop*);
IOSMetalFXInteropStatus IOSMetalFXInteropTexture(IOSMetalFXInterop*, const IOSMetalFXExportImage&, id<MTLTexture>*);
// No encoder may be active. Encodes a GPU wait for sceneReady=value.
// Caller supplies a command buffer from a distinct Metal queue. Using the
// exported Vulkan queue is rejected to avoid async-submission ordering deadlocks.
// Caller submits the Vulkan producer (signal) before dependent Vulkan consumer(wait).
IOSMetalFXInteropStatus IOSMetalFXInteropBegin(IOSMetalFXInterop*, id<MTLCommandBuffer>, uint64_t sceneReadyValue);
// After all MetalFX encoders end, encode metalDone=value. Does not commit.
// Caller submits Vulkan consumer waiting for this exact value before reading output.
IOSMetalFXInteropStatus IOSMetalFXInteropEnd(IOSMetalFXInterop*, id<MTLCommandBuffer>, uint64_t metalDoneValue);
#endif

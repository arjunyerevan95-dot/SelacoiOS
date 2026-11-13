#pragma once
#include <zvulkan/vulkaninstance.h> // Must establish Volk/VK_NO_PROTOTYPES before Vulkan headers.
#include <cstdint>
#include <cstdlib>
#include <cstring>
#if defined(__APPLE__)
#include <TargetConditionals.h>
#endif
inline bool IOSMetalFXRequested() {
#if defined(__APPLE__) && TARGET_OS_IPHONE
    const char* v=std::getenv("SELACO_IOS_METALFX"); return v && !std::strcmp(v,"1");
#else
    return false;
#endif
}
class VulkanDevice;
struct IOSMetalFXBackend;
struct IOSMetalFXVkFrame {
    VkImage color = VK_NULL_HANDLE, motion = VK_NULL_HANDLE, output = VK_NULL_HANDLE, reactive = VK_NULL_HANDLE;
    VkImageView depth = VK_NULL_HANDLE;
    uint32_t x=0,y=0,width=0,height=0,outputWidth=0,outputHeight=0;
    float jitterX=0,jitterY=0;
    bool completeMotion=false,reset=true;
    void (*flushProducer)(void*) = nullptr;
    void* user = nullptr;
};
// Frame images must already be GENERAL; caller must retain all Vulkan owners.
// Returns true only after GPU temporal work and the consumer queue wait are submitted.
// A false return leaves output undefined; caller must record the ordinary blit fallback.
bool IOSMetalFXBackendConsume(IOSMetalFXBackend*&, VulkanDevice*, const IOSMetalFXVkFrame&);
// Existing Vulkan fence retirement MUST cover all backend uses before destroy.
void IOSMetalFXBackendDestroy(IOSMetalFXBackend*);

void IOSMetalFXBackendRetire(IOSMetalFXBackend*&);

// Dedicated instance: do not reuse temporal backend pointer. All color inputs are
// post-tonemap output-size RGBA16Float, depth/motion retain low-res scene rectangle.
// Caller certifies consecutive real frames with no weapon/UI baked into either,
// plus a reserved generated/real presentation pair (FIFO timing feedback).
struct IOSMetalFXVkInterpolationFrame : IOSMetalFXVkFrame {
    VkImage previousColor=VK_NULL_HANDLE, ui=VK_NULL_HANDLE;
    // Optional exact current composite (weapons + HUD + the same postprocess).
    // Use with a matching clean color to synthesize a conservative opaque UI
    // influence patch. Translucent edges include current background by design.
    VkImage compositedColor=VK_NULL_HANDLE;
    bool matchedComposition=false;
    bool framegenComplete=false, cleanScenePair=false, previousFrameValid=false;
    bool presentationReserved=false;
    uint64_t previousFrameId=0,currentFrameId=0;
    float deltaTime=0,nearPlane=0,farPlane=0,verticalFovDegrees=0;
};
// Does not acquire/present a drawable or update caller's history. False => use real
// frame only and release presentation reservation. Fence retirement rules above apply.
bool IOSMetalFXBackendInterpolate(IOSMetalFXBackend*&,VulkanDevice*,const IOSMetalFXVkInterpolationFrame&);

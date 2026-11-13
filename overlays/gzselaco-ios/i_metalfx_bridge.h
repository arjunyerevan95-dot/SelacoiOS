#pragma once
// Objective-C++ bridge only. Caller owns Vulkan interop, GPU dependency ordering,
// resource lifetime, HUD composition and presentation. No submission is performed.
// Single render-thread ownership only. Destroy/reconfigure only after all associated
// GPU work completes. Caller must reset after GPU errors, camera cuts, load, resize,
// pause/resume or discontinuities. Temporal Encoded means encoded, not completed.
// Apple API baseline: temporal iOS16; interpolation iOS26/Xcode26 SDK.
// No iOS27-only properties (requiresPrevColorTexture, worldToViewMatrix) are used.
// https://developer.apple.com/documentation/metalfx/mtlfxtemporalscalerdescriptor
// https://developer.apple.com/documentation/metalfx/mtlfxframeinterpolatordescriptor
#ifdef __OBJC__
#import <Metal/Metal.h>
#include <cstdint>
struct IOSMetalFXConfig {
    uint32_t inputWidth, inputHeight, outputWidth, outputHeight;
    MTLPixelFormat colorFormat, depthFormat, motionFormat, outputFormat;
    MTLPixelFormat interpolationColorFormat, uiFormat;
    bool frameInterpolation;
    // Disable if upstream exposure is already applied to the input color.
    bool autoExposure = true;
};
struct IOSMetalFXFrame {
    id<MTLTexture> color, depth, motion, output;
    float jitterX = 0, jitterY = 0;
    // Current-to-previous motion in pixels when scale is one.
    float motionScaleX = 1, motionScaleY = 1, preExposure = 1;
    bool depthReversed = false, reset = false;
};
struct IOSMetalFXInterpolationFrame {
    // Tone-mapped output-resolution color, before UI; distinct previous frame.
    id<MTLTexture> color, previousColor, depth, motion, ui, output;
    float jitterX = 0, jitterY = 0, motionScaleX = 1, motionScaleY = 1;
    float deltaTime = 0, nearPlane = 0, farPlane = 0, verticalFovDegrees = 0;
    bool depthReversed = false, reset = false;
};
enum class IOSMetalFXStatus { Encoded, Ready, Unsupported, InvalidArgument, CreationFailed, HistoryRequired };
struct IOSMetalFXUsage {
    MTLTextureUsage color, depth, motion, output;
    MTLTextureUsage interpolationColor, interpolationDepth, interpolationMotion, interpolationUI, interpolationOutput;
};
struct IOSMetalFXBridge;
// ARC required. Link MetalFX weakly for pre-iOS16 deployment targets.
IOSMetalFXStatus IOSMetalFXCreate(id<MTLDevice>, const IOSMetalFXConfig&, IOSMetalFXBridge**);
void IOSMetalFXDestroy(IOSMetalFXBridge*);
IOSMetalFXUsage IOSMetalFXGetUsage(const IOSMetalFXBridge*);
IOSMetalFXStatus IOSMetalFXEncodeTemporal(IOSMetalFXBridge*, id<MTLCommandBuffer>, const IOSMetalFXFrame&);
IOSMetalFXStatus IOSMetalFXEncodeInterpolation(IOSMetalFXBridge*, id<MTLCommandBuffer>, const IOSMetalFXInterpolationFrame&);
#endif

#include "i_metalfx_bridge.h"
#import <MetalFX/MetalFX.h>
#include <cmath>
#if !__has_feature(objc_arc)
#error i_metalfx_bridge.mm requires ARC
#endif
#if defined(__IPHONE_OS_VERSION_MAX_ALLOWED) && __IPHONE_OS_VERSION_MAX_ALLOWED >= 260000
#define IOS_HAS_METALFX_INTERPOLATION 1
#else
#define IOS_HAS_METALFX_INTERPOLATION 0
#endif
struct IOSMetalFXBridge {
    IOSMetalFXConfig config;
    id<MTLDevice> device;
    id<MTLFXTemporalScaler> temporal API_AVAILABLE(ios(16.0));
#if IOS_HAS_METALFX_INTERPOLATION
    id<MTLFXFrameInterpolator> interpolator API_AVAILABLE(ios(26.0));
#endif
    IOSMetalFXUsage usage{};
    bool temporalHistory = false;
    bool interpolationResetPending = true;
};
static bool TextureOK(id<MTLTexture> t, id<MTLDevice> d, uint32_t w, uint32_t h,
                      MTLPixelFormat format, MTLTextureUsage usage) {
    return t && t.device == d && t.textureType == MTLTextureType2D && t.sampleCount == 1 &&
        t.width == w && t.height == h && t.pixelFormat == format &&
        (t.usage & usage) == usage && t.storageMode != MTLStorageModeMemoryless;
}
static bool CommandOK(id<MTLCommandBuffer> cb, id<MTLDevice> d) {
    return cb && cb.device == d && cb.status <= MTLCommandBufferStatusEnqueued;
}
IOSMetalFXStatus IOSMetalFXCreate(id<MTLDevice> device, const IOSMetalFXConfig& c, IOSMetalFXBridge** result) {
    if (!result) return IOSMetalFXStatus::InvalidArgument;
    *result = nullptr;
    if (!device || !c.inputWidth || !c.inputHeight || !c.outputWidth || !c.outputHeight)
        return IOSMetalFXStatus::InvalidArgument;
    if (@available(iOS 16.0, *)) {
        if (![MTLFXTemporalScalerDescriptor supportsDevice:device]) return IOSMetalFXStatus::Unsupported;
        if (c.frameInterpolation) {
#if IOS_HAS_METALFX_INTERPOLATION
            if (@available(iOS 26.0, *)) {
                if (![MTLFXFrameInterpolatorDescriptor supportsDevice:device]) return IOSMetalFXStatus::Unsupported;
            } else return IOSMetalFXStatus::Unsupported;
#else
            return IOSMetalFXStatus::Unsupported;
#endif
        }
        auto* b = new IOSMetalFXBridge{}; b->config = c; b->device = device;
        MTLFXTemporalScalerDescriptor* td = [MTLFXTemporalScalerDescriptor new];
        td.inputWidth = c.inputWidth; td.inputHeight = c.inputHeight;
        td.outputWidth = c.outputWidth; td.outputHeight = c.outputHeight;
        td.colorTextureFormat = c.colorFormat; td.depthTextureFormat = c.depthFormat;
        td.motionTextureFormat = c.motionFormat; td.outputTextureFormat = c.outputFormat;
        td.autoExposureEnabled = YES;
        b->temporal = [td newTemporalScalerWithDevice:device];
        if (!b->temporal) { delete b; return IOSMetalFXStatus::CreationFailed; }
        b->usage.color = b->temporal.colorTextureUsage; b->usage.depth = b->temporal.depthTextureUsage;
        b->usage.motion = b->temporal.motionTextureUsage; b->usage.output = b->temporal.outputTextureUsage;
#if IOS_HAS_METALFX_INTERPOLATION
        if (c.frameInterpolation) {
            if (@available(iOS 26.0, *)) {
                MTLFXFrameInterpolatorDescriptor* fd = [MTLFXFrameInterpolatorDescriptor new];
                fd.inputWidth = c.inputWidth; fd.inputHeight = c.inputHeight;
                fd.outputWidth = c.outputWidth; fd.outputHeight = c.outputHeight;
                fd.colorTextureFormat = c.interpolationColorFormat; fd.depthTextureFormat = c.depthFormat;
                fd.motionTextureFormat = c.motionFormat; fd.outputTextureFormat = c.interpolationColorFormat;
                fd.uiTextureFormat = c.uiFormat; fd.scaler = b->temporal;
                b->interpolator = [fd newFrameInterpolatorWithDevice:device];
                if (!b->interpolator) { delete b; return IOSMetalFXStatus::CreationFailed; }
                b->usage.interpolationColor = b->interpolator.colorTextureUsage;
                b->usage.interpolationDepth = b->interpolator.depthTextureUsage;
                b->usage.interpolationMotion = b->interpolator.motionTextureUsage;
                b->usage.interpolationUI = b->interpolator.uiTextureUsage;
                b->usage.interpolationOutput = b->interpolator.outputTextureUsage;
            }
        }
#endif
        *result = b; return IOSMetalFXStatus::Ready;
    }
    return IOSMetalFXStatus::Unsupported;
}
void IOSMetalFXDestroy(IOSMetalFXBridge* b) { delete b; }
IOSMetalFXUsage IOSMetalFXGetUsage(const IOSMetalFXBridge* b) { return b ? b->usage : IOSMetalFXUsage{}; }
IOSMetalFXStatus IOSMetalFXEncodeTemporal(IOSMetalFXBridge* b, id<MTLCommandBuffer> cb, const IOSMetalFXFrame& f) {
    if (!b || !CommandOK(cb,b->device)) return IOSMetalFXStatus::InvalidArgument;
    const auto& c = b->config; const auto& u = b->usage;
    if (!TextureOK(f.color,b->device,c.inputWidth,c.inputHeight,c.colorFormat,u.color) ||
        !TextureOK(f.depth,b->device,c.inputWidth,c.inputHeight,c.depthFormat,u.depth) ||
        !TextureOK(f.motion,b->device,c.inputWidth,c.inputHeight,c.motionFormat,u.motion) ||
        !TextureOK(f.output,b->device,c.outputWidth,c.outputHeight,c.outputFormat,u.output) ||
        f.output == f.color || f.output == f.depth || f.output == f.motion ||
        !std::isfinite(f.jitterX) || !std::isfinite(f.jitterY) || !std::isfinite(f.motionScaleX) ||
        !std::isfinite(f.motionScaleY) || !std::isfinite(f.preExposure) || f.preExposure <= 0)
        return IOSMetalFXStatus::InvalidArgument;
    if (@available(iOS 16.0, *)) {
        auto t = b->temporal; t.colorTexture = f.color; t.depthTexture = f.depth;
        t.motionTexture = f.motion; t.outputTexture = f.output;
        t.inputContentWidth = c.inputWidth; t.inputContentHeight = c.inputHeight;
        t.jitterOffsetX = f.jitterX; t.jitterOffsetY = f.jitterY;
        t.motionVectorScaleX = f.motionScaleX; t.motionVectorScaleY = f.motionScaleY;
        t.preExposure = f.preExposure; t.depthReversed = f.depthReversed;
        t.reset = f.reset || !b->temporalHistory;
        if (t.reset) b->interpolationResetPending = true;
        [t encodeToCommandBuffer:cb]; b->temporalHistory = true;
        return IOSMetalFXStatus::Encoded;
    }
    return IOSMetalFXStatus::Unsupported;
}
IOSMetalFXStatus IOSMetalFXEncodeInterpolation(IOSMetalFXBridge* b, id<MTLCommandBuffer> cb, const IOSMetalFXInterpolationFrame& f) {
#if IOS_HAS_METALFX_INTERPOLATION
    if (@available(iOS 26.0, *)) {
        if (!b || !CommandOK(cb,b->device)) return IOSMetalFXStatus::InvalidArgument;
        if (!b->config.frameInterpolation || !b->interpolator) return IOSMetalFXStatus::Unsupported;
        // Suppress synthetic frames on resets; renderer must present the real frame.
        if (f.reset || !f.previousColor || !b->temporalHistory) {
            b->interpolationResetPending = true; return IOSMetalFXStatus::HistoryRequired;
        }
        const auto& c=b->config; const auto& u=b->usage;
        if (!TextureOK(f.color,b->device,c.outputWidth,c.outputHeight,c.interpolationColorFormat,u.interpolationColor) ||
            !TextureOK(f.previousColor,b->device,c.outputWidth,c.outputHeight,c.interpolationColorFormat,u.interpolationColor) ||
            !TextureOK(f.depth,b->device,c.inputWidth,c.inputHeight,c.depthFormat,u.interpolationDepth) ||
            !TextureOK(f.motion,b->device,c.inputWidth,c.inputHeight,c.motionFormat,u.interpolationMotion) ||
            !TextureOK(f.ui,b->device,c.outputWidth,c.outputHeight,c.uiFormat,u.interpolationUI) ||
            !TextureOK(f.output,b->device,c.outputWidth,c.outputHeight,c.interpolationColorFormat,u.interpolationOutput) ||
            f.output == f.color || f.output == f.previousColor || f.output == f.ui || f.output == f.depth || f.output == f.motion || f.color == f.previousColor ||
            !std::isfinite(f.deltaTime) || f.deltaTime <= 0 || !std::isfinite(f.nearPlane) || f.nearPlane <= 0 ||
            !std::isfinite(f.farPlane) || f.farPlane <= f.nearPlane || !std::isfinite(f.verticalFovDegrees) ||
            f.verticalFovDegrees <= 0 || f.verticalFovDegrees >= 180 || !std::isfinite(f.jitterX) ||
            !std::isfinite(f.jitterY) || !std::isfinite(f.motionScaleX) || !std::isfinite(f.motionScaleY))
            return IOSMetalFXStatus::InvalidArgument;
        auto i=b->interpolator; i.colorTexture=f.color; i.prevColorTexture=f.previousColor;
        i.depthTexture=f.depth; i.motionTexture=f.motion; i.uiTexture=f.ui; i.outputTexture=f.output;
        i.jitterOffsetX=f.jitterX; i.jitterOffsetY=f.jitterY;
        i.motionVectorScaleX=f.motionScaleX; i.motionVectorScaleY=f.motionScaleY;
        i.depthReversed=f.depthReversed; i.deltaTime=f.deltaTime;
        i.nearPlane=f.nearPlane; i.farPlane=f.farPlane; i.fieldOfView=f.verticalFovDegrees;
        i.aspectRatio=float(c.outputWidth)/float(c.outputHeight);
        [i setIsUITextureComposited:NO]; i.shouldResetHistory=b->interpolationResetPending;
        [i encodeToCommandBuffer:cb]; b->interpolationResetPending=false; return IOSMetalFXStatus::Encoded;
    }
#else
    (void)b; (void)cb; (void)f;
#endif
    return IOSMetalFXStatus::Unsupported;
}

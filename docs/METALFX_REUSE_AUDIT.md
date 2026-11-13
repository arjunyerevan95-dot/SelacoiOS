# Existing GZDoom temporal / frame-generation code reuse

Inspected 2026-11-13. Source only; no downloaded software executed.

## Concrete projects

1. https://github.com/NightSightProductions/RTGL-D2-Metal
   Pinned inspected commit 1919834a514e15ed14cceaf716f4f572464758c9, metal-backend.
   LICENSE is MIT, copyrights Vasilii Shirokii (2024), Sultim Tsyrendashiev (2020-2023).
   - Source/Metal/MetalPathTracer.mm ~791: actual MetalFX temporal encode. UV motion scales by render width/height; renderer jitter sign is negated; automatic exposure disabled because upstream applies it.
   - Source/Metal/MetalDevice.mm ~847,1649: actual frame interpolation creation/encode, low-resolution depth/motion with output-resolution current and previous tone-mapped HUD-less color. Separate UI texture is used. Runtime guard macOS26, although whole app targets macOS27.
   - Source/Metal/MetalScene.mm ~974: prior primitive ID lookup, vertex/index count compatibility, previous model and vertex offsets; texture/topology changes mark no-history.
   - Source/Shaders/VertexData.inl ~403: previous dynamic positions plus previous transform, not only camera velocity.
   - Source/Shaders/HitInfo.inl ~349: current/previous projection and view matrices create current-to-previous screen motion.
   - Source/Metal/MetalDevice.mm presentation: late drawable acquisition and separate frame-generation presentation ownership. Not automatically usable with the existing Vulkan-owned swapchain.

2. https://github.com/vs-shirokii/gzdoom-rt
   Pinned inspected commit e618865ce47b40beb14e5b605d81d246416aa6b0. GPLv3.
   - src/common/rendering/rt/rt_state.h: push_uniqueid and primitive index scopes.
   - src/rendering/hwrenderer/scene/hw_sprites.cpp ~129: object identity scope at sprite submission.
   - Walls/flats/decals/portals/weapons also establish identity scopes.
   - This is a distinct RTGL path-tracing backend, not a drop-in velocity output patch for raster GZSelaco.

3. https://github.com/GPUOpen-Effects/FidelityFX-FSR2
   FSR2 is another reference for temporal input contracts, not a way to conjure absent moving-object vectors. Switching upscaler brands does not eliminate renderer history work.

## Changes made from this review

The native bridge's exposure behavior is configurable rather than hardwired auto-exposure. Final insertion point must pick its exposure convention deliberately. Reference independently confirms our separate UI and low-resolution depth/motion plus output-resolution color layout. No reference renderer code was copied wholesale and no macOS27-only API was added.

Primitive history helper adapts the prior-ID/topology/appearance pattern to raster CPU geometry. It remains a prerequisite until hooked to actual sprite/model submissions and velocity shader outputs. Missing histories must be marked, not masqueraded as valid zero motion.

## License and compatibility

Existing GZSelaco engine LICENSE is GPLv3. GPLv3 GZDoom RT material can be reused subject to its terms and preserving copyright/source obligations. MIT RTGL components can be reused with their notice. Proprietary DLSS binaries, retail archives, and unrelated Windows framegen injectors are not imported. Exact per-file notices must accompany any actual copying; API/reference observations alone are not redistributed code.

Existing code materially reduces design uncertainty but cannot replace required raster motion attachments, prior geometry history and Vulkan/Metal synchronization. No usable MetalFX build or performance claim follows from this audit.

Validation: temporal_primitive_history_test.cpp compiled on Linux with c++ -std=c++17 -Wall -Wextra -Werror and executed PASS on2026-11-13. No native SDK or GPU execution claimed. Cache payload bound is per-frame geometry only; map allocation overhead, previous+pending sets and owning returned vectors mean total memory can exceed that payload limit. Optimize storage/upload ownership before performance-sensitive runtime use.

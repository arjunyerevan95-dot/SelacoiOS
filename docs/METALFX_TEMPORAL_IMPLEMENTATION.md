# Temporal MetalFX and frame interpolation integration (in progress)

Status: implementation branch only, not wired into the app or built. No device claims.

## Architectural model

Pinned GZSelaco 95130c3 submits Vulkan through MoltenVK. SceneColor is RGBA16F; scene depth is a sampleable depth-stencil attachment. The iOS patch draws a reduced scene subrectangle into native allocations, then nearest-blits to PipelineImage before postprocessing. HUD/UI is drawn later. Presentation currently belongs to Vulkan swapchain.

Evidence: vk_renderbuffers.cpp, vk_postprocess.cpp::BlitSceneToPostprocess, patch-gzselaco-scene-scale.py, patch-gzselaco-present-lifetime.py. No velocity attachment or temporal projection/history implementation was found by focused search. Native allocations are not evidence of native scene shading.

Competing hypotheses: (1) shading/bandwidth dominates and temporal reconstruction helps; (2) scene traversal/actors/draw submission dominate and upscale alone cannot materially improve frame time. A device log must distinguish scene CPU duration, GPU scene/MetalFX duration, actual scene/drawable extents, real-rendered and generated-present counts. Generated FPS is never recorded as real render FPS.

## Feature contract

- MetalFX temporal is iOS16+; frame interpolation is iOS26+ (Apple DocC API availability). Compile frame interpolation with Xcode26/iOS26 SDK; weak link/availability checks preserve existing supported OS fallback.
- Check supportsDevice on each descriptor, then object creation; neither A18Pro hardware nor successful Vulkan initialization proves a feature was used.
- Temporal requires real camera AND object motion vectors, current depth, projection jitter, explicit reset on camera/map/resize/lifecycle discontinuity. A camera-only or zero-filled velocity image must not be represented as complete motion input.
- Render interpolation after tone mapping, with HUD kept separate; present one generated and one real frame with bounded queue and explicit timestamps.
- Vulkan/Metal ownership and semaphore/event synchronization must be documented and validated before enabling. No CPU texture readback, no per-frame queue/device idle workaround.
- Unsupported SDK/device, missing vectors, non-main views/unsupported portals, or invalid sizes must fail closed to the existing renderer. Disabled state is logged once with reason, never reported as MetalFX active.
- Existing saves, app identity and custom controls stay unchanged.

## Outstanding implementation boundaries

1. Native MetalFX object/resource bridge and validated Vulkan external-resource synchronization.
2. Previous-frame camera/object transforms plus velocity attachment, jitter and temporal resets.
3. Scene-only temporal output into postprocess, with color/exposure and reactive particle handling.
4. Tone-mapped frame history, separate HUD, interpolation and presentation ownership/pacing.
5. One integrated native compile/fixture pass once implementation is complete, then one guarded test IPA. No duplicate build dispatch.

## Sources

- https://developer.apple.com/documentation/metalfx/mtlfxtemporalscalerdescriptor
- https://developer.apple.com/documentation/metalfx/mtlfxframeinterpolatordescriptor
- https://developer.apple.com/videos/play/wwdc2025/211/
- https://developer.apple.com/metal/Metal-Feature-Set-Tables.pdf

## Local verification receipt (2026-11-13)

Portable temporal history/jitter fixture compiled with C++17, -Wall -Wextra -Werror and executed successfully on Linux. Cases: first frame, continuous frame, camera cut, view switch, resize, incomplete motion, timing discontinuity, explicit reset, invalid time, bounded jitter. This only validates state management, not MetalFX or rendering. Native Objective-C++ bridge still requires Xcode26 compile and GPU texture fixture before renderer wiring. No Actions run dispatched for this work.

Checkpoint 2: opt-in source patches now add a camera-only RG16F velocity attachment/pass plus previous-camera shader outputs, queried timeline feature/instance Metal export declarations, and native compile inclusion patch. GPU interop module exports real textures/shared events and encodes GPU wait/signal. Patches applied together to pinned engine fixture and source-contract checks passed. Camera-only diagnostic explicitly reports completeMotion=0 and is NOT fed into temporal/framegen. Objective-C++, Vulkan C++ and shaders remain uncompiled; no build or feature enablement claimed. Actual moving geometry/jitter/history consumption, submit barriers and generated-frame presentation remain unfinished.

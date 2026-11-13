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

## Current checkpoint (2026-11-13, candidate 7308926)

The earlier entries above are historical, not the current feature state. The native
bridge, external-resource synchronization, sprite/model/portal history producers,
reactive MRT, jitter and supported-frame temporal consumption are now wired into
an opt-in engine candidate. Run 43444218232 passed its Xcode26 API compilation and
input validation; the full app build was still in progress at this checkpoint.
No on-device MetalFX execution or performance result has been verified.

The test launcher enables temporal only. Frame interpolation has a compiled
native encoder/backend and bounded timing interface, but is NOT connected to
engine presentation and is deliberately disabled. This is not the completed
user-requested temporal-plus-framegen feature.

### Concrete remaining framegen integration

Inspection of pinned engine 95130c3 plus this candidate confirms:
- VkPostprocess::PostProcessScene runs Pass1 (exposure/custom-beforebloom/bloom),
  then DrawEndScene2D (weapon sprites), then Pass2 (tonemap/colormap/lens/FXAA/
  custom-scene). Its final pipeline image is NOT weapon-free.
- VulkanRenderDevice::Update draws the HUD later with Draw2D, clears that list,
  ends the frame and retires commands. HUD replay must occur before list clear,
  not by assuming a second late callback can recover it.
- Separately tone-mapping a transparent weapon texture is not equivalent to
  tone-mapping the existing composited scene. Nonlinear postprocess and custom
  scene shaders must not silently change semantics in a framegen experiment.
- The remaining solution must retain a clean scene pair and correctly composite
  weapon/HUD over both outputs, with distinct acquired-image/semaphore lifetimes.
  A native encoder call alone does not establish these contracts.
- Existing timed-present interface requires supported FIFO timing feedback;
  MAILBOX availability in the regular port does not prove this framegen pacing
  path is supported. Query and reject unsupported devices rather than queue an
  unbounded or competing Metal presenter.

These are implementation tasks, not reasons to ask the user to perform extra
piecemeal phone tests. The regular temporal candidate remains independently
useful and preserves ordinary rendering fallback while framegen is completed.

## Framegen continuation after temporal delivery

Staged (not included in master stack or shipped IPA):
- `patch-gzselaco-metalfx-pair-present.py` adds actual intermediate Vulkan submit/
  present plus a distinct second acquire semaphore. Independent review confirmed
  the chain/fence design but found missing swapchain-generation and explicit
  present-error propagation. DO NOT call or enable this draft until those are
  resolved; a missing feedback ID must not strand a pacer reservation.
- Native interpolation backend now accepts a certified matching clean/composited
  pair, synthesizes an opaque one-pixel-dilated influence overlay on the GPU and
  passes it to MetalFX. Real composite remains untouched. This avoids invalid
  independent weapon tonemapping. It may repeat small current-background patches
  around transparent weapon/HUD edges on generated frames.
- CPU composition identity/dilation contract passed. New Metal kernel and new
  presentation changes are NOT SDK/device compiled. No new build dispatched.
- Still required: dual deterministic Pass2 scene capture/history, correct full
  composite capture including HUD, complete renderer callsite, loss handling,
  combined native validation and on-device evidence.

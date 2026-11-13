# Temporal consumer integration status

`patch-gzselaco-metalfx-consume.py` installs an actual consumer into
`VkPostprocess::BlitSceneToPostprocess`, before ordinary postprocessing/UI. It:

- Adds export intent to Vulkan images/views when the Metal-object extension is enabled.
- Adds storage usage only to opt-in pipeline images.
- Handles GENERAL-layout access transitions in the existing transition helper.
- Creates two exportable timeline semaphores and a separate native Metal queue.
- GPU-crops color and motion and converts sampled depth to low-resolution R32Float.
- Calls the native temporal encoder, writing to the existing Vulkan pipeline image.
- Orders Vulkan producer, native compute/upscale and Vulkan consumer with GPU timelines.
- Uses existing fence retirement for replacement/destruction, with no new CPU waits.

This is not presented as functional end-to-end: `SelacoMotionMetadata().complete`
remains false. No diagnostic attachment, environment variable or user toggle may
promote that certification. Motion producer owns jitter, reset and completeness.
Unsupported viewport geometry falls back; first integration is full screen only.
Dimension changes defer replacement until existing fence retirement.

Frame generation is NOT routed by this patch. Its source must be correctly
post-tonemap and separated from both UI and weapon layers, with their appropriate
motion handling. Existing final image is not automatically a safe framegen input.

Failure policy: failures before producer submission discard unsubmitted native work
and retain ordinary rendering. Failed Vulkan signal/wait submissions after flush
are fatal. Native GPU command-buffer error terminates from the completion thread;
otherwise its missing GPU timeline signal could deadlock the Vulkan consumer. It
never host-signals invalid output as a successful frame. This policy requires device
validation and is not a promised recovery path.

Validation completed: Python AST and exact source patch anchors applied against
pinned engine-derived fixture; patched ImageBuilder/ViewBuilder host-compiled with
MSVC, including the Metal-export preprocessor branch (opaque Metal types). The
fixture's CMake source-list anchor was isolated, not full CMake generation.
Apple Objective-C++, Metal shader runtime compilation and actual queue/texture
execution have NOT yet been validated. A single bounded Apple SDK compile is next.

## Follow-on frame interpolation and reactive coverage (not yet SDK revalidated)
The separate IOSMetalFXBackendInterpolate endpoint now performs real native
interpolation encoding with the same GPU timeline handoff. It requires consecutive
validated previous/current frame IDs, clean scene textures, separate UI, explicit
motion/framegen completeness and a reserved presentation pair. No engine caller
currently produces that clean pair or routes both outputs to presentation.

Temporal consumption now exports/crops the R8 SceneReactive mask and configures
MetalFX reactive-mask input with iOS17.4 availability guards. Uses
reactiveTextureUsage (17.4), not the newer reactiveMaskTextureUsage property.
These later changes are not covered by the earlier successful native compile.

## Backend review after b267c23
Crop inputs now explicitly require shader-read usage and exact RG16Float motion,
RGBA16Float scene color and R8Unorm reactive format before submitting any work.
Frame interpolation rejects duplicate/out-of-order submitted real-frame IDs;
explicit reset clears that sequence and suppresses the reset frame. Both endpoints
remain single-render-thread-owned. Their producer queue submission must not race
another submitter on the same Vulkan queue (Vulkan external synchronization).

Reactive availability: descriptor reactiveMaskTextureEnabled/Format and scaler
reactiveTextureUsage are guarded by both SDK >= iOS17.4 and runtime17.4. The similarly
named reactiveMaskTextureUsage is iOS27-only and intentionally not used. Failure
before producer submission permits fallback. Failure after GPU handoff is fatal,
including completion-thread abort on Metal failure to prevent an unsignalled wait.

Minimal renderer route still required: retain clean post-tonemap real-frame pair,
render weapon/UI to a separate compositing layer, encode into a distinct exportable
RGBA16Float output, and present generated+real through the existing Vulkan swapchain
with actual timing feedback. Merely taking the current post-Pass2 texture is unsafe:
it already contains weapons drawn by afterBloomDrawEndScene2D. First bounded route
could accept only positively weapon-free scenes, render Draw2D separately, and reject
all other frames; normal armed gameplay requires proper weapon-layer separation.
The endpoint itself does not reserve/present swapchain images or certify this route.

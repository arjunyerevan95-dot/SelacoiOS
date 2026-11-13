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

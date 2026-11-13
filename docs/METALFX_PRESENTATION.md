# MetalFX generated-frame pacing boundary

The existing Vulkan swapchain remains the sole drawable owner. Creating a second
CAMetalLayer presenter beside MoltenVK is intentionally not used. The optional
`patch-gzselaco-metalfx-present.py` adds actual `VK_GOOGLE_display_timing` desired
presentation times and timing-feedback queries to the pinned swapchain code;
ordinary QueuePresent callers keep their previous behavior.

Frame generation must require advertised timing support, FIFO presentation,
90 Hz or higher observed refresh, and approximately two refresh intervals per
real frame. Current default MAILBOX is not adequate to promise both generated and
real frames are displayed; do not silently enable interpolation there.

`IOSTemporalPresentPacer` reserves only one generated/real pair at once. The caller
must retain both source textures, wait semaphores, and acquired swapchain images
until their appropriate GPU/presentation retirement, present generated then real
with separate IDs, and retire the pair from actual timing feedback, not graphics
fence completion. Unsupported timing, late real frames, reset history or missing
motion means ordinary real-frame-only presentation. Missing feedback must cause a
drain/reset and real-only recovery, never an unbounded queue. Nanosecond times must
be in the platform monotonic presentation clock, not epoch time.

Status: source patch applied to exact pinned source. Altered vulkanswapchain.cpp
compiled as C++17 with MSVC; standalone pacing assertions compiled /W4 /WX and
passed. These are host checks, not an iOS/MoltenVK presentation test. No framegen
pair caller is connected yet. No performance or latency gain is established.

Remaining integration: preserve post-tonemap HUD-less real textures, render HUD
separately, encode interpolation, acquire/submit two images with independent
semaphores, query timing feedback, and drain safely across resize/background.
Frame generation itself does not reduce input latency and adds historical delay.

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

## Paired submission lifecycle
`PresentIntermediate` returns Rejected (no successful acquire), Submitted (timed
pair queued, visibility still unknown), or Draining (successful acquire consumed
but reservation became invalid). It checks swapchain generation and refresh timing
before and after acquisition. Invalid acquired output is replaced by an ordinary
real-frame draw, submitted and presented without timing; the binary acquire signal
is never abandoned. The final real acquire rechecks the generation and timing too.

QueuePresent returns VkResult through both layers. Suboptimal/out-of-date/lost
results invalidate the pair rather than promise future timing feedback. The caller
must always complete ordinary WaitForCommands(true) after Submitted or Draining.
An exceptional invalid pair increments PairDrainEpoch ONLY after normal GPU fence
retirement and a successful device-queue drain. The pacing owner compares that epoch
and cancels the stale reservation; never reinterpret cancellation as display proof.
Successful pairs continue to retire exclusively through real presentation feedback.
This code does not implement a second CAMetalLayer owner or enable frame generation.

Validated: exact-source materialization, source-contract fixture and MSVC compilation
of patched ZVulkan swapchain. Engine command-manager Apple compilation and real WSI
lost-surface/recreation behavior still need validation. Device idle is not evidence
that any frame became visible; per-image presentation semaphore lifetime remains
managed by the existing swapchain implementation.

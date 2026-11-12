# MetalFX feasibility assessment

Current path: GZSelaco Vulkan through MoltenVK. No motion-vector output was found in the Vulkan renderer/shaders; SSAO jitter is not temporal projection jitter.

Spatial upscaling is a plausible next step once scene resolution and HUD composition are separated. It needs compatible Metal textures, Vulkan/Metal resource lifetime and queue synchronization, color-space/format handling, runtime support checks, and measurement against the initial Vulkan blit. It is not implemented by the scene-scale patch.

Temporal scaling needs depth, motion vectors, projection jitter and history/reset management. Frame interpolation needs two rendered frames, depth and motion vectors plus presentation pacing. These require substantial renderer additions; extra displayed frames do not increase game simulation responsiveness. No FPS promise or hardware-support claim is made without runtime checks.

Official references consulted 2026-11-12:
- https://developer.apple.com/documentation/metalfx
- https://developer.apple.com/videos/play/wwdc2025/211/
- https://developer.apple.com/metal/Metal-Feature-Set-Tables.pdf

Priority: validate lower 3D workload with native HUD, then measure bottlenecks before adding MetalFX complexity.

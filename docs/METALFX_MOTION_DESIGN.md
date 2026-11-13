# MetalFX motion, jitter and history implementation design

Status: source inspection and design only. NONE of the renderer changes below is implemented by this document. Native MetalFX bridge work is separate and does not establish that correct scene motion or frame generation is integrated.

Source: public pinned GZSelaco 95130c3. No retail archives inspected. Paths below are relative to that engine checkout. Source anchors must be rechecked after cumulative iOS patch application.

## Current architectural model

The Vulkan main scene has color/depth and optional fog/normal attachments. Current scene scaling uses a smaller viewport within native attachments, then enlarges color before native postprocessing and HUD. Current transforms exist, but previous-render-frame transforms and a velocity attachment do not. SSAO jitter is not temporal camera jitter. MetalFX therefore cannot receive correct motion merely by exposing existing textures.

Supporting anchors:
- src/common/rendering/hwrenderer/data/hw_viewpointuniforms.h:16-36 holds current projection/view/normal matrices only.
- src/common/rendering/vulkan/shaders/vk_shader.cpp:165 declares corresponding ViewpointUBO. CPU and shader layouts must change together.
- src/rendering/hwrenderer/hw_entrypoint.cpp:169-174 sets eye projection then calls SetupView.
- src/rendering/hwrenderer/scene/hw_drawinfo.cpp:396-401 constructs view matrix.
- wadsrc/static/shaders/glsl/main.vp:48-55 and projection assignment near122 transform current deformed vertex to clip space. Vulkan depth conversion follows.
- wadsrc/static/shaders/glsl/main.fp:17-20 and911-913 output color plus optional fog/normal, not motion.

## Smallest correct stage ordering

1. Add an opt-in temporal context and explicit reset policy, but leave feature unavailable until all mandatory inputs exist. Store unjittered current and previous main-view projection/view, actual scene extent and offset, frame serial, jitter and history validity. Do not call a placeholder or camera-only bridge complete.
2. Add a dedicated RG16F velocity attachment and temporal shader/pass permutation independent of SSAO. Update render pass formats, framebuffer attachments, write/blend masks, barriers and lifetime together. Add main-view jitter only; retain unjittered matrices for velocity computation and CPU visibility where required. Define input-pixel/UV motion convention, sign and Y orientation once and verify against Apple API inputs.
3. Static opaque geometry: compute current and previous clip positions from corresponding unjittered view-projection and identical world positions. This provides a narrowly correct static-world implementation, not correct whole-game motion.
4. Add previous rendered geometry for sprites, moving geometry and models. Only after these work can the main opaque scene claim valid object motion. Do not substitute prior game-tick transforms for previous displayed/rendered-frame state.
5. Add portal/mirror history and transparency/reactivity policy, or explicitly reject history for unsupported regions. Integrate upscale before native HUD and maintain UI-free color for frame interpolation.
6. Enable temporal only after input contract and device diagnostics pass. Frame interpolation additionally needs consecutive correctly timed frames, depth/motion, HUD treatment and pacing. Native API success alone is not visual validation.

## Motion data by primitive type

### Sprites

src/rendering/hwrenderer/scene/hw_sprites.cpp:816-817 interpolates actor position and895 angles. CreateVertices at591-607 constructs and allocates current world-space billboard corners. Current corners projected with a previous camera cannot recover actor translation, rotation or billboard orientation changes.

Required: stable actor identity plus generation and prior rendered quad/corner state, including previous billboard basis, dimensions and offsets. Preserve correct UV correspondence. Split sprites must inherit the same primitive history and interpolate corresponding previous corners. Reject history for newly visible/spawned or structurally changed sprites; do not reuse stale pooled actor addresses as identity. Animation atlas changes need conservative reactivity, because geometry motion does not describe changing texture content.

### Models

src/rendering/hwrenderer/hw_models.cpp:117-119 sets animation interpolation. SetupFrame at144-157 uploads bones and chooses morph frames. main.vp applies current bones and interpolates frames before ModelMatrix. Current draw state contains only current deformation.

Required: cache previous rendered object-to-world, morph-frame indices/interpolation fraction and bone palette for each stable renderable instance. Vertex shader must evaluate previous deformation, then previous model and camera transforms. A previous model matrix alone fails on animated limbs. Reset on model/topology replacement, missing previous pose or discontinuous motion. HUD models are separate; do not let their alternate projection contaminate scene history.

### Moving world geometry

Static-world reprojection is not correct for moving doors, floors or walls. Geometry producers need matching previous rendered positions or a per-surface transform where representable. Reactive/reject fallback must be explicit for unsupported geometry, not a fake zero vector. Verify how vertex buffers are regenerated and whether stable sector/line/surface IDs can map old positions before choosing storage.

### Particles and transparency

Transient particles need stable history or rejection/reactivity. Alpha-blended surfaces usually do not represent a single depth/motion layer. Preserve opaque depth/motion, and mark changed transparent coverage using a dedicated reactive input where supported by the selected MetalFX API. Derive mask values from actual material/coverage behavior; do not reuse another upscaler's tuned mask blindly. A reactive mask mitigates history artifacts but does not manufacture correct vectors for frame interpolation. Unsupported effects may require compositing after upscale/interpolation or documented interpolation exclusion.

## Portals and mirrors

src/rendering/hwrenderer/scene/hw_portal.cpp calls SetupView around559,639,701,798,860 for transformed views. hw_drawinfo.cpp:948-955 renders portals after opaque geometry and before translucency.

Required: previous portal-specific projection/view keyed by stable recursion path and transform identity, including mirrors. One global previous camera matrix misprojects portal content. For a first guarded implementation, explicit portal-region history rejection is safer than invented vectors; it must be reported as a limitation and checked for seams. Portal depth can be repurposed/cleared during stencil rendering, so verify the depth delivered to MetalFX actually corresponds to final color.

## Jitter, depth and HUD boundaries

Apply sample jitter after main projection creation in hw_entrypoint.cpp, before main scene drawing, not globally to every HWViewpointBuffer upload. Do not jitter 2D, camera targets or save screenshots. Track unjittered matrices separately. Account for Vulkan clip-depth conversion in main.vp and the actual reduced scene subrectangle.

hw_drawinfo.cpp:767-768 and851-852 use separate HUD projections. hw_entrypoint.cpp invokes PostProcessScene with DrawEndScene2D callback after EndDrawScene. The precise location of weapon sprites versus HUD 3D models must be preserved rather than assuming all HUD drawing occurs at one point.

Depth creation is in src/common/rendering/vulkan/textures/vk_renderbuffers.cpp:185-214 and already has a depth-only view. Native Metal compatibility and depth convention must still be verified. Match depth, motion and scene color extents before handing them to MetalFX; native-sized backing images alone do not establish matching contents.

## Vulkan plumbing anchors

- src/common/rendering/vulkan/renderer/vk_renderpass.cpp:180 has a fixed three-format attachment array.
- Same file:251/255 selects GBUFFER_PASS by draw-buffer count. Adding motion must not accidentally enable SSAO-dependent shaders.
- src/common/rendering/vulkan/textures/vk_renderbuffers.cpp:233-251 normal allocation is a template, not a substitute, for velocity allocation.
- Vulkan shader manager must compile matching temporal vertex/fragment permutations, including effect shaders, and preserve fallback paths.

## Reset and ownership requirements

Reset temporal and interpolation history on new map/load, camera change or teleport, resize/orientation, resolution change, background/resume, toggle, incompatible projection, missing prior pose and renderer/device recreation. Track rendered-frame serial independently of simulation ticks. Retain every input texture until GPU consumers finish, with Vulkan-Metal synchronization rather than CPU readback. Do not reuse previous frame storage while interpolation reads it.

## Focused acceptance evidence

Required fixtures: stationary camera/moving sprite; moving camera/static scene; animated model with stationary root; moving door; billboard rotation; portal/mirror; transparent smoke; HUD text/weapon; resize and resume. Debug markers should include history reset reason, scene/depth/motion extents, jitter, consecutive frame serials, motion path coverage and whether temporal/interpolation actually encoded.

Competing hypothesis to test: apparent ghosting may be wrong vector sign/scale/jitter rather than insufficient object history. A static-world pan distinguishes convention errors; stationary-camera moving actors distinguish missing object vectors. Camera-only depth reprojection can be a diagnostic stage, but is not a production-complete solution for Selaco.

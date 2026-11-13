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

## Implemented reusable primitive cache (2026-11-13)

`overlays/gzselaco-ios/i_temporal_primitive_history.h` now implements the CPU-side matching/storage component. This is NOT a renderer velocity integration. Matching design was adapted from RTGL `Source/Metal/MetalScene.mm` at1919834a514e15ed14cceaf716f4f572464758c9; its MIT notice is retained in `RTGL-MIT-LICENSE.txt`.

The key includes object ID, lifetime generation, view/portal-path ID and primitive ID. Geometry stores owning post-deformation world positions, index connectivity, topology revision and appearance revision. It refuses invalid indices/nonfinite positions, unmatched identity, changed connectivity/topology/appearance and ambiguous duplicate IDs. Begin/Capture/Commit separates actually completed render history from aborted work. Missing primitives expire each committed frame; serial gaps reset history. Byte and entry bounds limit retained CPU data. Callers must check FrameUnambiguous before encoding vectors because a later duplicate invalidates earlier matches.

`tests/temporal_primitive_history_test.cpp` covers previous rendered positions, result lifetime, identity components, same-count topology changes, appearance, duplicate submission, serial gaps, disappearing objects, invalid input and memory budget. Validation: compiled and executed successfully on Legion using MSVC 14.44 /std:c++17 /EHsc /W4; parent independently compiled with C++17 -Wall -Wextra -Werror and executed on cloud. No iOS or device validation is claimed.

Still required runtime hooks:
- Allocate stable object generations and primitive/view keys in Selaco sprite/model/world/portal producers. GZDoom RT routes unique IDs through rtstate into RgMeshInfo (rt_main.cpp around1602), but those IDs cannot simply be assumed present or sufficiently generation-safe in Selaco.
- Extract current post-deformation model positions (or use GPU previous-pose buffers instead of this CPU cache); preserve sprite correspondence and moving-world surfaces. This header does not evaluate bones or reconstruct positions.
- Upload matching previous world positions alongside current vertices and write their projected difference into a velocity render target. Prior/current unjittered camera transforms remain external.
- Aggregate any rejection into reactive/history validity coverage; never interpret a missing vector as zero motion. Caller must mark unsupported particle/portal/transparent paths explicitly.
- Commit only after frame construction succeeds; invalidate on discontinuities. GPU resource retirement and upload ring lifetime remain external responsibilities.


## Camera-only raster diagnostic patch (2026-11-13)

Implemented `scripts/patch-gzselaco-temporal-motion.py`, applied to an isolated pinned95130c3 engine worktree. It introduces an opt-in `SELACO_MOTION_DIAGNOSTIC=1` iOS path and a dedicated RG16F fourth color attachment with matching renderpass format, framebuffer slot, clear value and nonblended write state. Main shaders emit previous-minus-current projected UV motion; both CPU viewpoint layout and Vulkan/OpenGL UBO declarations gain previous camera matrices. Previous main-view matrices are captured after scene processing; first view/camera identity changes or elapsed gaps reject camera history. This remains incomplete history handling, not the final reset mechanism.

This patch is intentionally labeled CAMERA-ONLY DIAGNOSTIC. `SelacoMotionComplete()` returns false. It neither enables MetalFX nor claims usable whole-scene temporal input. Dynamic geometry, portal-view reprojection, transient materials and some special effect shaders remain incorrect/unwritten. The fourth target is diagnostic storage only; no production consumer or texture transition to a MetalFX read has been connected. It has no projection jitter yet. Special-effect/transparent pixels need explicit validity coverage before consumption.

Validation performed: Python syntax, exact source-anchor application to pinned source, git diff whitespace check, and `tests/temporal_motion_patch_test.py` source-contract assertions. These are NOT C++/GLSL compilation, cumulative iOS patch application, Vulkan validation, native build or phone evidence. No workflow changed or build dispatched. Before merging into a runnable feature, compile actual generated shader permutations, verify fourth-attachment limits and unsupported effect coverage, apply after existing scene-scale patches, and finish object histories/jitter/reset/interop.

Additional compatibility check: existing patch-gzselaco-scene-scale.py followed by temporal-motion patch applied successfully to isolated pinned source; source-contract checks and diff check pass. Full cumulative platform patch stack and native compilation remain unverified.


## Moving billboard and portal-camera runtime hooks (2026-11-13)

patch-gzselaco-temporal-sprites.py applies after temporal-motion. It now captures previous rendered world-space billboard corners in HWSprite::CreateVertices, with actor lifetime generation, texture/UV appearance and fixed quad-topology matching. A sidecar generation registry is explicitly forgotten from DObject destruction, preventing simple address reuse from inheriting history. Per-sprite draw temporarily uploads previous corners and vertex-base/validity in viewpoint UBO; GLSL uses gl_VertexIndex to select the corresponding previous world corner. The original viewpoint binding is restored after each draw. Duplicate/split submissions, particles and portal sprites are rejected; model draws explicitly reject because previous bone/morph data is absent. This is actual generated runtime source, but has not been compiled as the full engine or validated on-device.

patch-gzselaco-temporal-views.py adds per-recursion-path previous camera matrices at SetupView. Keys preserve the ordered portal source chain rather than hashing it; history resets on main-camera/time discontinuity and commits after completed main-scene processing. This makes portal camera matrices available, but final portal depth correspondence and moving portal sprites remain unsupported: portal rendering still marks coverage rejected. Portal source lifetime across map reload needs final scene-epoch reset work.

Public metadata in hw_motion_diagnostic.h is SelacoMotionMetadata(): jitterX/jitterY in input pixels (currently both zero, no jitter implementation), reset, complete, and framegenComplete. Both completeness fields remain false. Framegen completeness is separate because post-upscale weapon drawing before tone mapping is not represented in world velocity; hiding ordinary Draw2D HUD alone does not fix that.

Validation: new sprite-runtime and view-history C++ tests compiled and executed on Legion with MSVC C++17 /W4 /WX. They cover real previous corners, lifetime generation changes, duplicate capture, resets, ordered portal keys and missing paths. Exact pinned-source patch application in scene-scale -> temporal-motion -> temporal-sprites -> temporal-views order and source-wiring checks pass. These checks are not native engine/shader compilation or GPU evidence. No workflow edits, pushes or build dispatch.

## Model rigid and skeletal previous-pose source path

New additive patch-gzselaco-temporal-models.py captures previous model transform, bone palette, interpolation factor, current morph-frame pair, skin, draw identity and actor generation. Previous bones are uploaded through the existing BoneBuffer; vertex shader evaluates the previous pose using those matrices and the previous interpolation factor. This is valid only when current vertex attributes still describe the same morph-frame pair. Frame transitions, changed skin/count, unsupported HUD/portal model paths and missing palette data reject. Bone-copy work is gated behind the motion diagnostic toggle; cache caps individual and aggregate bone counts.

CPU history test passed MSVC C++17 /W4 /WX. Patcher applied to the isolated fixture. Full C++/shader/native compilation is pending; not included in the earlier SDK checkpoint.

Remaining whole-world blocker is concrete: hw_vertexbuilder.cpp UpdatePlaneVertices rewrites persistent plane vertices in place, and dynamic walls/polyobjects regenerate geometry without prior vertex streams. Correct sprite/model vectors alone do not establish complete scene coverage. Frame-level rejection can cover observed UpdatePlaneVertices/AddPolyobjs paths, but unknown shader effects, transparent/depth coverage and jitter/reset requirements still prevent safely enabling a full temporal path today.

## Reactive mask, jitter and observed world rejection

New additive patches temporal-world-guards and temporal-reactive-jitter attach source hooks for observed in-place sector-plane updates, polyobject rendering and unsupported flat hacks/translucency. Those paths reject coverage rather than pretending static-camera motion is complete. No previous wall/plane vertex reconstruction is implemented.

Reactive source plumbing allocates SceneReactive (R8_UNORM) as fifth MRT, adds matching format/framebuffer/clear slots and MAX-union blending. Main material shader marks sprites, invalid model history and alpha-blended pixels conservatively; nondefault/user material shaders receive a reactive define. Special-effect draws that may not write all outputs reject coverage. This mask is a temporal history hint, not substitute depth/velocity for frame interpolation.

Optional SELACO_TEMPORAL_JITTER=1 applies actual input-pixel Halton jitter to raster clip coordinates after unjittered motion outputs have been computed. Previous/current matrices remain unjittered; metadata reports input-pixel offsets. Default off while full consumption/coverage is unfinished; enabling jitter alone may visibly shimmer without temporal resolve. Runtime output orientation and Apple sign convention still require validation.

Source-contract tests and patch application pass; full engine/shader/device validation remains pending. Before allowing supported-frame temporal, finalize coverage at scene resolve, remember rejected frames and force history reset on recovery (camera history otherwise differs from last MetalFX input), audit unsupported draw paths and verify every mask pixel. Framegen remains separately incomplete due post-upscale weapon coverage.

## Supported-frame candidate and rejection fallback (unverified on device)
The final source order is motion, sprites, views, models, world guards, reactive/jitter, MetalFX consume, supported-frame candidate, Vulkan inverse-jitter fallback. The master script enforces this ordering.

The candidate decides eligibility only at the scene resolve boundary after observed draw coverage. It records history only after a successful backend consume, resetting on gaps, failures, epoch changes and extent changes. Engine view interpolation resets increment the epoch. Frame-generation completeness remains false.

Jitter is allowed only for the scaled fullscreen single-sample Vulkan path. A rejected/failed temporal frame uses an independent Vulkan linear scene sampling pass, source position plus the recorded pixel jitter, clamped to the crop's half-texel interior. This removes the raster translation even without MetalFX availability; it is not temporal reconstruction. All pinned scene vertex shader entries use main.vp. Device testing must still verify orientation, edge behavior and artifacts.

Runtime opt-in requires SELACO_MOTION_DIAGNOSTIC=1, SELACO_TEMPORAL_JITTER=1 and SELACO_TEMPORAL_SUPPORTED_FRAMES=1 plus the backend's separate temporal request. None is a claim of complete game-wide support. Portals, observed moving planes/polyobjects, missing object history, changed morph topology and incomplete MRT coverage fall back. Current validations cover portable history tests and exact source patch application; native full-engine and GPU shader compilation are still required.

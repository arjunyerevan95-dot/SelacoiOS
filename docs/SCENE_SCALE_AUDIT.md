# Scene-only resolution candidate

`patch-gzselaco-scene-scale.py` modifies exact Vulkan anchors. Apply after the platform source materialization; launcher patch keeps its original native drawable pixel calculation and passes selection through SELACO_IOS_SCENE_SCALE before starting the engine.

The scene renders into a smaller subrectangle of native-sized SceneColor/depth/normal/fog attachments. Pipeline images, final presentation and engine virtual dimensions remain native. Before postprocessing a nearest-filter Vulkan blit enlarges only the scene subrectangle into its original native rectangle, then restores the native scene rectangle. Bloom/tonemap, ordinary weapon sprites and subsequent HUD/menu drawing retain native pipeline resolution. HUD 3D models drawn before that boundary remain reduced-resolution.

MSAA and SSAO are explicitly disabled each frame while scene scaling is active. This avoids an invalid resizing resolve and avoids changed depth/normal sample coordinates. Saves use separate buffers and are excluded. Camera targets are not resized. Only the main screen target is scaled. Attachments remain native-sized: this saves scene fragment shading work, not attachment memory or native postprocessing cost. The filter is deliberately nearest, not a promised smooth reconstruction filter. No input geometry is changed.

Actual attachment/pipeline extent, reduced scene extent and offsets, native scene extent and disabled features print when dimensions change. This diagnostic distinguishes scene reduction from a smaller final drawable. The feature is activated only on Apple builds with the launch environment set, otherwise existing behavior remains intact.

Local validation: exact build23 source-anchor patch application, Python syntax and source-contract assertions, rectangle bounds across four native sizes, four scales and full/reduced viewports. These are NOT shader execution, C++ compilation or a Vulkan/Metal device test. Before calling verified, test in-game HUD/codex/menu, reduced screenblocks, portals/cameras, weapon sprites/models, pause/resume, screenshot/save path, and confirm diagnostics. Native attachments plus single-sample deliberately minimize renderpass changes.

Integration review: force global vid_scalefactor=1 and vid_scalemode=0 while scene scaling is active. Clear the native pipeline image to black before partial blit and add transfer-write ordering, so reduced-screenblocks borders are defined.

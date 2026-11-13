#!/usr/bin/env python3
"""Source wiring only; actual shader/device validation remains required."""
from pathlib import Path
import sys
r=Path(sys.argv[1])
def has(p,*needles):
 s=(r/p).read_text()
 for n in needles:assert n in s,(p,n)
has('src/common/rendering/vulkan/textures/vk_renderbuffers.cpp','SceneReactive.Image','VK_FORMAT_R8_UNORM')
has('src/common/rendering/vulkan/renderer/vk_renderpass.cpp','VK_BLEND_OP_MAX','VK_FORMAT_R16G16_SFLOAT, VK_FORMAT_R8_UNORM')
has('src/common/rendering/vulkan/renderer/vk_renderstate.cpp','if (key.DrawBuffers > 4)','pipelineKey.SpecialEffect > EFF_NONE')
has('wadsrc/static/shaders/glsl/main.fp','FragReactiveCoverage','SELACO_REACTIVE_MATERIAL')
has('wadsrc/static/shaders/glsl/main.vp','gl_Position.xy += MotionJitter.xy * gl_Position.w;','MotionPreviousPosition()')
has('src/rendering/hwrenderer/hw_entrypoint.cpp','SELACO_TEMPORAL_JITTER','2.f*jx/sw','SelacoMotionMetadataStorage() = {jx,jy,!motionHistory,false};')
has('src/rendering/hwrenderer/hw_vertexbuilder.cpp','prior world stream absent')
has('src/rendering/hwrenderer/scene/hw_bsp.cpp','previous instance geometry absent')
print('PASS reactive/jitter/world-reject source contract only')

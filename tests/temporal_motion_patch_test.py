#!/usr/bin/env python3
"""Source-contract checks only. Does not compile or execute Vulkan/Metal."""
from pathlib import Path
import sys
r=Path(sys.argv[1])
def require(path,*needles):
 s=(r/path).read_text()
 for n in needles: assert n in s,(path,n)
require('src/common/rendering/hwrenderer/data/hw_motion_diagnostic.h','SELACO_MOTION_DIAGNOSTIC','TARGET_OS_IPHONE','SelacoMotionComplete() { return false; }')
require('src/common/rendering/hwrenderer/data/hw_viewpointuniforms.h','mPreviousProjectionMatrix','mPreviousViewMatrix')
for backend in ['vulkan/shaders/vk_shader.cpp','gl/gl_shader.cpp']:
 require('src/common/rendering/'+backend,'mat4 PreviousProjectionMatrix;','mat4 PreviousViewMatrix;')
require('src/common/rendering/vulkan/textures/vk_renderbuffers.cpp','VK_FORMAT_R16G16_SFLOAT','SceneMotionDiagnostic.Reset(fb)','if (SelacoMotionDiagnostic())','CameraOnlyMotionDiagnosticView')
require('src/common/rendering/vulkan/renderer/vk_renderstate.cpp','if (key.DrawBuffers > 3)\n\t\t\tbuilder.AddAttachment(buffers->SceneMotionDiagnostic.View.get());','if (key.DrawBuffers > 3)\n\t\tbeginInfo.AddClearColor')
require('src/common/rendering/vulkan/renderer/vk_renderpass.cpp','buffers->SceneNormalFormat, VK_FORMAT_R16G16_SFLOAT','motionBlend.ColorWriteMask')
require('src/rendering/hwrenderer/hw_entrypoint.cpp','completeMotion=0; temporal/framegen unavailable','motionPrevView = di->VPUniforms.mViewMatrix','motionCamera == camera')
require('wadsrc/static/shaders/glsl/main.vp','vMotionPreviousClip = PreviousProjectionMatrix * PreviousViewMatrix * worldcoord;')
require('wadsrc/static/shaders/glsl/main.fp','layout(location=3) out vec2 FragMotionDiagnostic;','MUST NOT feed completeMotion=true','vMotionPreviousClip.xy/vMotionPreviousClip.w - vMotionCurrentClip.xy/vMotionCurrentClip.w')
print('PASS source contract only: diagnostic MRT; completeMotion=false')

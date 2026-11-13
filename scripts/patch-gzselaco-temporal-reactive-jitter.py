#!/usr/bin/env python3
"""Reactive MRT + optional true projection-jitter plumbing, still guarded."""
from pathlib import Path
import sys
r=Path(sys.argv[1]);e={}
def edit(p,a,b):
 s=e.get(p,(r/p).read_text());assert s.count(a)==1,(p,a[:65],s.count(a));e[p]=s.replace(a,b)
b='src/common/rendering/'
edit(b+'hwrenderer/data/hw_renderstate.h','SelacoMotionDiagnostic() ? 4 : 3','SelacoMotionDiagnostic() ? 5 : 3')
edit(b+'hwrenderer/data/hw_viewpointuniforms.h','\tVSMatrix mPreviousProjectionMatrix;','\tFVector4 mMotionJitter = {0,0,0,0};\n\tVSMatrix mPreviousProjectionMatrix;')
for rel,tabs in [('vulkan/shaders/vk_shader.cpp','\t\t'),('gl/gl_shader.cpp','\t\t\t')]:
 edit(b+rel,tabs+'mat4 PreviousProjectionMatrix;',tabs+'vec4 MotionJitter;\n'+tabs+'mat4 PreviousProjectionMatrix;')
p=b+'vulkan/textures/vk_renderbuffers.h'
edit(p,'\tVkTextureImage SceneMotionDiagnostic;','\tVkTextureImage SceneMotionDiagnostic;\n\tVkTextureImage SceneReactive;')
p=b+'vulkan/textures/vk_renderbuffers.cpp'
edit(p,'\tSceneMotionDiagnostic.Reset(fb);','\tSceneMotionDiagnostic.Reset(fb);\n    SceneReactive.Reset(fb);')
edit(p,'        CreateSceneMotionDiagnostic(width, height, samples);','''        CreateSceneMotionDiagnostic(width, height, samples);
        SceneReactive.Image=ImageBuilder().Size(width,height).Samples(samples)
            .Format(VK_FORMAT_R8_UNORM).Usage(VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_SAMPLED_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT)
            .DebugName("TemporalReactiveCoverage").Create(fb->device.get());
        SceneReactive.View=ImageViewBuilder().Image(SceneReactive.Image.get(),VK_FORMAT_R8_UNORM)
            .DebugName("TemporalReactiveCoverageView").Create(fb->device.get());
        VkImageTransition().AddImage(&SceneReactive,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,true).Execute(fb->GetCommands()->GetDrawCommands());''')
p=b+'vulkan/renderer/vk_renderpass.cpp'
edit(p,'buffers->SceneNormalFormat, VK_FORMAT_R16G16_SFLOAT };','buffers->SceneNormalFormat, VK_FORMAT_R16G16_SFLOAT, VK_FORMAT_R8_UNORM };')
edit(p,'        if (i == 3) {','''        if (i == 4) {
            ColorBlendAttachmentBuilder reactiveBlend;
            reactiveBlend.ColorWriteMask(VK_COLOR_COMPONENT_R_BIT);
            reactiveBlend.BlendMode(VK_BLEND_OP_MAX,VK_BLEND_FACTOR_ONE,VK_BLEND_FACTOR_ONE);
            builder.AddColorBlendAttachment(reactiveBlend.Create());
        } else if (i == 3) {''')
p=b+'vulkan/renderer/vk_renderstate.cpp'
edit(p,'\t\tif (key.DepthStencil)\n\t\t\tbuilder.AddAttachment(mRenderTarget.DepthStencil);','\t\tif (key.DrawBuffers > 4)\n\t\t\tbuilder.AddAttachment(buffers->SceneReactive.View.get());\n\t\tif (key.DepthStencil)\n\t\t\tbuilder.AddAttachment(mRenderTarget.DepthStencil);')
edit(p,'\tbeginInfo.AddClearDepthStencil(1.0f, 0);','\tif (key.DrawBuffers > 4)\n\t\tbeginInfo.AddClearColor(0.0f,0.0f,0.0f,0.0f);\n\tbeginInfo.AddClearDepthStencil(1.0f, 0);')
edit(p,'#include "vk_renderstate.h"','#include "vk_renderstate.h"\n#include "hwrenderer/data/i_motion_sprite_runtime.h"')
edit(p,'\t// Is this the one we already have?','''    // Special shaders may not emit velocity/reactive outputs; reject rather
    // than assuming those attachments describe their final color.
    if(SelacoMotionDiagnostic() && mRenderTarget.DrawBuffers > 3 && pipelineKey.SpecialEffect > EFF_NONE && pipelineKey.ColorMask)
        SelacoMotionRuntime::Reject();
\t// Is this the one we already have?''')
p=b+'vulkan/shaders/vk_shader.cpp'
for prefix in ['prog','natprog']:
 anchor=f'\t\t{prefix}.frag = LoadFragShader(defaultshaders[i].ShaderName, mainfp, defaultshaders[i].gettexelfunc, defaultshaders[i].lightfunc, defaultshaders[i].Defines,'
 repl=f'\t\tFString reactiveDefines=defaultshaders[i].Defines;\n\t\tif(i!=0)reactiveDefines += "#define SELACO_REACTIVE_MATERIAL\\n";\n\t\t{prefix}.frag = LoadFragShader(defaultshaders[i].ShaderName, mainfp, defaultshaders[i].gettexelfunc, defaultshaders[i].lightfunc, reactiveDefines.GetChars(),'
 # Keep C++ escaped newline inside quoted define.
 repl=repl.replace('MATERIAL\n";','MATERIAL\\n";')
 edit(p,anchor,repl)
edit(p,'\t\tFString defines = defaultshaders[usershaders[i].shaderType].Defines + usershaders[i].defines;','\t\tFString defines = defaultshaders[usershaders[i].shaderType].Defines + usershaders[i].defines;\n        defines += "#define SELACO_REACTIVE_MATERIAL\\n";')
p='wadsrc/static/shaders/glsl/main.fp'
edit(p,'layout(location=3) out vec2 FragMotionDiagnostic;','layout(location=3) out vec2 FragMotionDiagnostic;\nlayout(location=4) out float FragReactiveCoverage;')
edit(p,'    FragMotionDiagnostic = vec2(0.0);','''    FragReactiveCoverage=(MotionSpriteInfo.x>0.5 || (MotionModelInfo.x>0.5 && MotionModelInfo.y<0.5) || frag.a<0.999) ? 1.0 : 0.0;
#ifdef SELACO_REACTIVE_MATERIAL
    FragReactiveCoverage=1.0;
#endif
    FragMotionDiagnostic = vec2(0.0);''')
p='wadsrc/static/shaders/glsl/main.vp'
edit(p,'\tgl_Position.z = (gl_Position.z + gl_Position.w) / 2.0;','\tgl_Position.xy += MotionJitter.xy * gl_Position.w;\n\tgl_Position.z = (gl_Position.z + gl_Position.w) / 2.0;')
p='src/rendering/hwrenderer/hw_entrypoint.cpp'
edit(p,'#include <chrono>','#include <chrono>\n#include "hwrenderer/data/i_temporal_history.h"\n#include <cstdlib>')
edit(p,'            SelacoMotionMetadataStorage() = {0.f,0.f,!motionHistory,false};','''            static unsigned motionJitterIndex=0;
            if(!motionHistory)motionJitterIndex=0;
            const char* jitterOption=std::getenv("SELACO_TEMPORAL_JITTER");
            const bool useJitter=jitterOption && jitterOption[0]=='1' && jitterOption[1]==0;
            const auto jitter=SelacoTemporal::SampleJitter(motionJitterIndex++);
            const float jx=useJitter?jitter.x:0.f,jy=useJitter?jitter.y:0.f;
            const int sw=screen->mSceneViewport.width,sh=screen->mSceneViewport.height;
            di->VPUniforms.mMotionJitter={sw>0?2.f*jx/sw:0.f,sh>0?2.f*jy/sh:0.f,jx,jy};
            SelacoMotionMetadataStorage() = {jx,jy,!motionHistory,false};''')
for p,s in e.items():(r/p).write_text(s)
overlay=Path(__file__).resolve().parents[1]/'overlays/gzselaco-ios'
(r/(b+'hwrenderer/data/i_temporal_history.h')).write_text((overlay/'i_temporal_history.h').read_text(encoding='utf-8-sig'))
print('Applied reactive coverage MRT + optional unjittered-motion/raster-jitter path; completeness still guarded')

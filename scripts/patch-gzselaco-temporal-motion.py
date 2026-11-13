#!/usr/bin/env python3
"""Pinned GZSelaco camera-only velocity MRT diagnostic. NOT complete MetalFX input.
Default off; only SELACO_MOTION_DIAGNOSTIC=1 activates this iOS-only path.
No consumer may set completeMotion from this diagnostic attachment.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1]); edits={}
def edit(rel,old,new):
    s=edits.get(rel,(root/rel).read_text())
    assert s.count(old)==1,(rel,old[:70],s.count(old))
    edits[rel]=s.replace(old,new)
base='src/common/rendering/'
helper='''#pragma once
#include <cstdlib>
#if defined(__APPLE__)
#include <TargetConditionals.h>
#endif
inline bool SelacoMotionDiagnostic() {
#if defined(__APPLE__) && TARGET_OS_IPHONE
    static const bool enabled = [] { const char* p=std::getenv("SELACO_MOTION_DIAGNOSTIC"); return p && p[0]=='1' && p[1]==0; }();
    return enabled;
#else
    return false;
#endif
}
// Camera-only raster diagnostic: intentionally never a complete motion field.
inline bool SelacoMotionComplete() { return false; }
'''
edit(base+'hwrenderer/data/hw_renderstate.h','#include "vectors.h"','#include "vectors.h"\n#include "hw_motion_diagnostic.h"')
edit(base+'hwrenderer/data/hw_renderstate.h','return mPassType == GBUFFER_PASS ? 3 : 1;','return mPassType == GBUFFER_PASS ? (SelacoMotionDiagnostic() ? 4 : 3) : 1;')
edit(base+'hwrenderer/data/hw_viewpointuniforms.h','\tVSMatrix mProjectionMatrix;','\tVSMatrix mPreviousProjectionMatrix;\n\tVSMatrix mPreviousViewMatrix;\n\tVSMatrix mProjectionMatrix;')
for rel,tabs in [('vulkan/shaders/vk_shader.cpp','\t\t'),('gl/gl_shader.cpp','\t\t\t')]:
    edit(base+rel,tabs+'mat4 ProjectionMatrix;',tabs+'mat4 PreviousProjectionMatrix;\n'+tabs+'mat4 PreviousViewMatrix;\n'+tabs+'mat4 ProjectionMatrix;')
# Main-view camera history, deliberately excludes camera targets/save shots.
p='src/rendering/hwrenderer/hw_entrypoint.cpp'
edit(p,'#include "gi.h"','#include "gi.h"\n#include "hwrenderer/data/hw_motion_diagnostic.h"\n#include <chrono>')
edit(p,'bool useSSAO = (gl_ssao != 0);','bool useSSAO = (gl_ssao != 0) || (toscreen && SelacoMotionDiagnostic());')
anchor='\t\tdi->SetupView(RenderState, vp.Pos.X, vp.Pos.Y, vp.Pos.Z, false, false);'
edit(p,anchor,anchor+'''
        // Previous RENDERED main-view camera, not previous simulation tick.
        // Dynamic objects/portals are NOT represented: diagnostic only.
        static VSMatrix motionPrevProjection, motionPrevView;
        static const void* motionCamera = nullptr;
        static std::chrono::steady_clock::time_point motionTime{};
        const auto motionNow = std::chrono::steady_clock::now();
        const bool motionActive = mainview && toscreen && SelacoMotionDiagnostic();
        const bool motionHistory = motionActive && motionCamera == camera &&
            std::chrono::duration<double>(motionNow-motionTime).count() < 0.25;
        di->VPUniforms.mPreviousProjectionMatrix = motionHistory ? motionPrevProjection : di->VPUniforms.mProjectionMatrix;
        di->VPUniforms.mPreviousViewMatrix = motionHistory ? motionPrevView : di->VPUniforms.mViewMatrix;
        if (motionActive) {
            di->vpIndex = screen->mViewpoints->SetViewpoint(RenderState, &di->VPUniforms);
            static bool motionAnnounced = false;
            if (!motionAnnounced) { Printf("Selaco motion MRT: CAMERA-ONLY DIAGNOSTIC; completeMotion=0; temporal/framegen unavailable\\n"); motionAnnounced = true; }
        }
''')
# vpIndex access verified below; uses normal viewpoint rebinding.
edit(p,'\t\tdi->EndDrawInfo();','''        if (motionActive) {
            motionPrevProjection = di->VPUniforms.mProjectionMatrix;
            motionPrevView = di->VPUniforms.mViewMatrix;
            motionCamera = camera; motionTime = motionNow;
        }
\t\tdi->EndDrawInfo();''')
p=base+'vulkan/textures/vk_renderbuffers.h'
edit(p,'\tVkTextureImage SceneFog;','\tVkTextureImage SceneFog;\n\tVkTextureImage SceneMotionDiagnostic;')
edit(p,'\tvoid CreateSceneFog(int width, int height, VkSampleCountFlagBits samples);','\tvoid CreateSceneMotionDiagnostic(int width, int height, VkSampleCountFlagBits samples);\n\tvoid CreateSceneFog(int width, int height, VkSampleCountFlagBits samples);')
p=base+'vulkan/textures/vk_renderbuffers.cpp'
edit(p,'#include "vk_renderbuffers.h"','#include "vk_renderbuffers.h"\n#include "hwrenderer/data/hw_motion_diagnostic.h"')
edit(p,'\tSceneFog.Reset(fb);','\tSceneFog.Reset(fb);\n\tSceneMotionDiagnostic.Reset(fb);')
edit(p,'\tCreateSceneFog(width, height, samples);','''\tCreateSceneFog(width, height, samples);
    if (SelacoMotionDiagnostic()) {
        CreateSceneMotionDiagnostic(width, height, samples);
        VkImageTransition().AddImage(&SceneMotionDiagnostic, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL, true).Execute(fb->GetCommands()->GetDrawCommands());
    }''')
edit(p,'void VkRenderBuffers::CreateSceneFog(int width, int height, VkSampleCountFlagBits samples)','''void VkRenderBuffers::CreateSceneMotionDiagnostic(int width, int height, VkSampleCountFlagBits samples)
{
    SceneMotionDiagnostic.Image = ImageBuilder().Size(width,height).Samples(samples)
        .Format(VK_FORMAT_R16G16_SFLOAT)
        .Usage(VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_SAMPLED_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT)
        .DebugName("CameraOnlyMotionDiagnostic").Create(fb->device.get());
    SceneMotionDiagnostic.View = ImageViewBuilder().Image(SceneMotionDiagnostic.Image.get(),VK_FORMAT_R16G16_SFLOAT)
        .DebugName("CameraOnlyMotionDiagnosticView").Create(fb->device.get());
}

void VkRenderBuffers::CreateSceneFog(int width, int height, VkSampleCountFlagBits samples)''')
p=base+'vulkan/renderer/vk_renderpass.cpp'
edit(p,'buffers->SceneNormalFormat };','buffers->SceneNormalFormat, VK_FORMAT_R16G16_SFLOAT };')
anchor='\tfor (int i = 0; i < PassKey.DrawBuffers; i++)\n\t\tbuilder.AddColorBlendAttachment(blendbuilder.Create());'
edit(p,anchor,'''    for (int i = 0; i < PassKey.DrawBuffers; i++) {
        if (i == 3) {
            // No alpha blending of velocity. Translucency is still incomplete.
            ColorBlendAttachmentBuilder motionBlend;
            motionBlend.ColorWriteMask(VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT);
            builder.AddColorBlendAttachment(motionBlend.Create());
        } else builder.AddColorBlendAttachment(blendbuilder.Create());
    }''')
p=base+'vulkan/renderer/vk_renderstate.cpp'
edit(p,'\t\tif (key.DepthStencil)\n\t\t\tbuilder.AddAttachment(mRenderTarget.DepthStencil);','\t\tif (key.DrawBuffers > 3)\n\t\t\tbuilder.AddAttachment(buffers->SceneMotionDiagnostic.View.get());\n\t\tif (key.DepthStencil)\n\t\t\tbuilder.AddAttachment(mRenderTarget.DepthStencil);')
edit(p,'\tbeginInfo.AddClearDepthStencil(1.0f, 0);','\tif (key.DrawBuffers > 3)\n\t\tbeginInfo.AddClearColor(0.0f, 0.0f, 0.0f, 0.0f);\n\tbeginInfo.AddClearDepthStencil(1.0f, 0);')
p='wadsrc/static/shaders/glsl/main.vp'
edit(p,'layout(location = 9) out vec3 vLightmap;','''layout(location = 9) out vec3 vLightmap;
#ifdef VULKAN_COORDINATE_SYSTEM
layout(location = 10) out vec4 vMotionCurrentClip;
layout(location = 11) out vec4 vMotionPreviousClip;
#endif''')
edit(p,'\tgl_Position = ProjectionMatrix * eyeCoordPos;','''\tgl_Position = ProjectionMatrix * eyeCoordPos;
#ifdef VULKAN_COORDINATE_SYSTEM
    vMotionCurrentClip = gl_Position;
    vMotionPreviousClip = PreviousProjectionMatrix * PreviousViewMatrix * worldcoord;
#endif''')
p='wadsrc/static/shaders/glsl/main.fp'
edit(p,'layout(location = 9) in vec3 vLightmap;','''layout(location = 9) in vec3 vLightmap;
#ifdef VULKAN_COORDINATE_SYSTEM
layout(location = 10) in vec4 vMotionCurrentClip;
layout(location = 11) in vec4 vMotionPreviousClip;
#endif''')
edit(p,'layout(location=2) out vec4 FragNormal;','''layout(location=2) out vec4 FragNormal;
#ifdef VULKAN_COORDINATE_SYSTEM
layout(location=3) out vec2 FragMotionDiagnostic;
#endif''')
edit(p,'\tFragNormal = vec4(vEyeNormal.xyz * 0.5 + 0.5, 1.0);','''\tFragNormal = vec4(vEyeNormal.xyz * 0.5 + 0.5, 1.0);
#ifdef VULKAN_COORDINATE_SYSTEM
    // UV previous-minus-current. Jitter is not yet enabled in this diagnostic.
    // No object deformation history: MUST NOT feed completeMotion=true.
    FragMotionDiagnostic = vec2(0.0);
    if (vMotionPreviousClip.w > 0.00001 && vMotionCurrentClip.w > 0.00001)
        FragMotionDiagnostic = 0.5 * (vMotionPreviousClip.xy/vMotionPreviousClip.w - vMotionCurrentClip.xy/vMotionCurrentClip.w);
#endif''')
# Fail before writing on mismatched source. Idempotence intentionally rejects.
for rel,s in edits.items(): (root/rel).write_text(s)
(root/(base+'hwrenderer/data/hw_motion_diagnostic.h')).write_text(helper)
print('Applied camera-only MRT diagnostic; completeMotion=false; not MetalFX integration')

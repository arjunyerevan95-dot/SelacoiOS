#!/usr/bin/env python3
"""Inverse-jitter Vulkan scene fallback, independent of MetalFX availability."""
from pathlib import Path
import sys
r=Path(sys.argv[1]);e={}
def edit(p,a,b):
 s=e.get(p,(r/p).read_text());assert s.count(a)==1,(p,a[:70],s.count(a));e[p]=s.replace(a,b)
p='src/common/rendering/vulkan/renderer/vk_postprocess.h'
edit(p,'\tIOSMetalFXBackend* iosMetalFX = nullptr;','\tIOSMetalFXBackend* iosMetalFX = nullptr;\n    PPShader motionFallback;')
p='src/common/rendering/vulkan/renderer/vk_postprocess.cpp'
edit(p,'VkPostprocess::VkPostprocess(VulkanRenderDevice* fb) : fb(fb)\n{\n}', '''struct MotionFallbackUniforms {
    FVector2 Scale,Offset,Minimum,Maximum;
    static std::vector<UniformFieldDesc> Desc() { return {
        {"Scale",UniformType::Vec2,offsetof(MotionFallbackUniforms,Scale)},
        {"Offset",UniformType::Vec2,offsetof(MotionFallbackUniforms,Offset)},
        {"Minimum",UniformType::Vec2,offsetof(MotionFallbackUniforms,Minimum)},
        {"Maximum",UniformType::Vec2,offsetof(MotionFallbackUniforms,Maximum)}
    }; }
};
VkPostprocess::VkPostprocess(VulkanRenderDevice* fb) : fb(fb)
{
    motionFallback.FragmentShader="shaders/pp/motionfallback.fp";
    motionFallback.Uniforms=MotionFallbackUniforms::Desc();
}''')
anchor='#endif\n\tVkImageTransition()\n\t\t.AddImage(&buffers->SceneColor, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, false)'
edit(p,anchor,'''    // A rejected/failed temporal frame was already rasterized with jitter.
    // Vulkan linear sampling removes that fractional translation without MetalFX.
    if(SelacoMotionDiagnostic() && fb->iosSceneScaled &&
       buffers->GetSceneSamples()==VK_SAMPLE_COUNT_1_BIT &&
       (temporalMetadata.jitterX!=0.f || temporalMetadata.jitterY!=0.f)) {
        const auto& src=fb->mSceneViewport;
        const float iw=1.f/buffers->GetWidth(),ih=1.f/buffers->GetHeight();
        MotionFallbackUniforms u;
        u.Scale={src.width*iw,src.height*ih};
        u.Offset={(src.left+temporalMetadata.jitterX)*iw,(src.top+temporalMetadata.jitterY)*ih};
        u.Minimum={(src.left+0.5f)*iw,(src.top+0.5f)*ih};
        u.Maximum={(src.left+src.width-0.5f)*iw,(src.top+src.height-0.5f)*ih};
        VkPPRenderState fallback(fb);
        fallback.Clear();fallback.Shader=&motionFallback;fallback.Uniforms.Set(u);
        fallback.Viewport=fb->iosNativeSceneRect;
        fallback.SetInputSceneColor(0,PPFilterMode::Linear,PPWrapMode::Clamp);
        fallback.SetOutputCurrent();fallback.SetNoBlend();fallback.Draw();
        return;
    }
#endif
\tVkImageTransition()
\t\t.AddImage(&buffers->SceneColor, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, false)''')
# Jitter only the viewport path supported by the inverse transform.
p='src/rendering/hwrenderer/hw_entrypoint.cpp'
edit(p,"const bool useJitter=jitterOption && jitterOption[0]=='1' && jitterOption[1]==0;",
"const bool useJitter=jitterOption && jitterOption[0]=='1' && jitterOption[1]==0 && SelacoMotionJitterAllowed();")
p='src/common/rendering/hwrenderer/data/hw_motion_diagnostic.h'
edit(p,'struct SelacoMotionFrameMetadata {','inline bool& SelacoMotionJitterAllowed(){static bool allowed=false;return allowed;}\nstruct SelacoMotionFrameMetadata {')
p='src/common/rendering/vulkan/system/vk_renderdevice.cpp'
edit(p,'void VulkanRenderDevice::SetSceneRenderTarget(bool useSSAO)\n{\n    iosSceneScaled = false;','void VulkanRenderDevice::SetSceneRenderTarget(bool useSSAO)\n{\n    iosSceneScaled = false;\n    SelacoMotionJitterAllowed()=false;')
edit(p,'\tmRenderState->SetRenderTarget(&GetBuffers()->SceneColor, GetBuffers()->SceneDepthStencil.View.get(), GetBuffers()->GetWidth(), GetBuffers()->GetHeight(), VK_FORMAT_R16G16B16A16_SFLOAT, GetBuffers()->GetSceneSamples());\n}\n\nbool VulkanRenderDevice::RaytracingEnabled()','    SelacoMotionJitterAllowed()=iosSceneScaled && GetBuffers()->GetSceneSamples()==VK_SAMPLE_COUNT_1_BIT && iosNativeSceneRect.left==0 && iosNativeSceneRect.top==0 && iosNativeSceneRect.width==GetBuffers()->GetWidth() && iosNativeSceneRect.height==GetBuffers()->GetHeight();\n\tmRenderState->SetRenderTarget(&GetBuffers()->SceneColor, GetBuffers()->SceneDepthStencil.View.get(), GetBuffers()->GetWidth(), GetBuffers()->GetHeight(), VK_FORMAT_R16G16B16A16_SFLOAT, GetBuffers()->GetSceneSamples());\n}\n\nbool VulkanRenderDevice::RaytracingEnabled()')
for p,s in e.items():(r/p).write_text(s)
(r/'wadsrc/static/shaders/pp/motionfallback.fp').write_text('''// Inverse raster translation; not temporal reconstruction or frame generation.
layout(location=0) in vec2 TexCoord;
layout(location=0) out vec4 FragColor;
layout(binding=0) uniform sampler2D SceneTexture;
void main() {
    FragColor=texture(SceneTexture,clamp(Offset+TexCoord*Scale,Minimum,Maximum));
}
''')
print('Installed Vulkan fractional inverse-jitter fallback')

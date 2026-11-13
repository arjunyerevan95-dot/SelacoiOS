#!/usr/bin/env python3
"""Dual clean/full frame capture for future frame interpolation. No FG enablement.
Apply after experimental stack; full real scene retains original postprocess.
Unknown custom scene/screen effects reject the duplicate clean branch.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1]);edits={}
def edit(rel,old,new):
 p=root/rel;s=edits.get(p,p.read_text());assert s.count(old)==1,(rel,old[:60]);edits[p]=s.replace(old,new)
b='src/common/rendering/'
edit(b+'hwrenderer/postprocessing/hw_postprocess.h','\tvoid Run(PPRenderState *renderstate, FString target);','\tvoid Run(PPRenderState *renderstate, FString target);\n\tbool HasEnabled(FString target);')
edit(b+'hwrenderer/postprocessing/hw_postprocess.cpp','void PPCustomShaders::CreateShaders()','''bool PPCustomShaders::HasEnabled(FString target)
{
 if(!gl_custompost) return false;
 CreateShaders();
 for(auto& shader:mShaders) if(shader->Desc->Target==target && shader->Desc->Enabled) return true;
 return false;
}

void PPCustomShaders::CreateShaders()''')
edit(b+'vulkan/renderer/vk_postprocess.h','\tvoid RetireMetalFX();','''\tvoid RetireMetalFX();
\tvoid CaptureFramegenComposite();
\tbool HasFramegenPair() const { return framegenPairReady; }
\tVkTextureImage* FramegenClean(bool previous=false) { return &framegenClean[previous ? 1-framegenIndex : framegenIndex]; }
\tVkTextureImage* FramegenComposite() { return &framegenComposite; }''')
edit(b+'vulkan/renderer/vk_postprocess.h','    PPShader motionFallback;','''    PPShader motionFallback;
    bool temporalConsumed=false,framegenCaptured=false,framegenPairReady=false;
    uint64_t framegenSerial=0,framegenPreviousSerial=0;
    unsigned framegenIndex=0;
    VkTextureImage framegenSnapshot,framegenClean[2],framegenComposite;
    void EnsureFramegenTexture(VkTextureImage& image);
    void CopyFramegenImage(VkTextureImage& source,VkTextureImage& destination);
    bool CaptureFramegenClean(int fixedcm,float flash,int width,int height);''')
edit(b+'vulkan/renderer/vk_postprocess.cpp','\tmCurrentPipelineImage = 0;','\tmCurrentPipelineImage = 0;\n\ttemporalConsumed=false;')
edit(b+'vulkan/renderer/vk_postprocess.cpp','        if(consumed){','        if(consumed){\n            temporalConsumed=true;')
edit(b+'vulkan/renderer/vk_postprocess.cpp','\thw_postprocess.Pass1(&renderstate, fixedcm, sceneWidth, sceneHeight);','''\thw_postprocess.Pass1(&renderstate, fixedcm, sceneWidth, sceneHeight);
\t// Snapshot AFTER exposure/bloom, then run clean Pass2 without replaying Pass1.
\tCaptureFramegenClean(fixedcm,flash,sceneWidth,sceneHeight);''')
edit(b+'vulkan/renderer/vk_postprocess.cpp','#include \"flatvertices.h\"','#include \"flatvertices.h\"\n#include <cstring>')
anchor='void VkPostprocess::BlitSceneToPostprocess()'
body='''void VkPostprocess::EnsureFramegenTexture(VkTextureImage& image)
{
 auto buffers=fb->GetBuffers();
 if(image.Image && image.Image->width==buffers->GetWidth() && image.Image->height==buffers->GetHeight())return;
 image.Reset(fb);
 framegenPreviousSerial=0;
 image.Image=ImageBuilder().Size(buffers->GetWidth(),buffers->GetHeight())
  .Format(VK_FORMAT_R16G16B16A16_SFLOAT)
  .Usage(VK_IMAGE_USAGE_TRANSFER_SRC_BIT|VK_IMAGE_USAGE_TRANSFER_DST_BIT|VK_IMAGE_USAGE_SAMPLED_BIT|VK_IMAGE_USAGE_STORAGE_BIT)
  .DebugName("FramegenCompositionCapture").Create(fb->device.get());
 image.View=ImageViewBuilder().Image(image.Image.get(),VK_FORMAT_R16G16B16A16_SFLOAT)
  .DebugName("FramegenCompositionCaptureView").Create(fb->device.get());
}

void VkPostprocess::CopyFramegenImage(VkTextureImage& source,VkTextureImage& destination)
{
 fb->GetRenderState()->EndRenderPass();
 auto cmd=fb->GetCommands()->GetDrawCommands();
 VkImageTransition().AddImage(&source,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,false)
  .AddImage(&destination,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,true).Execute(cmd);
 VkImageCopy region={};region.srcSubresource.aspectMask=region.dstSubresource.aspectMask=VK_IMAGE_ASPECT_COLOR_BIT;
 region.srcSubresource.layerCount=region.dstSubresource.layerCount=1;
 region.extent={uint32_t(source.Image->width),uint32_t(source.Image->height),1};
 cmd->copyImage(source.Image->image,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
  destination.Image->image,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,1,&region);
 VkImageTransition().AddImage(&destination,VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,false).Execute(cmd);
}

bool VkPostprocess::CaptureFramegenClean(int fixedcm,float flash,int width,int height)
{
 framegenCaptured=false;framegenPairReady=false;
 const char* option=std::getenv("SELACO_IOS_METALFX_FRAMEGEN");
 const auto meta=SelacoMotionMetadata();
 const auto serial=SelacoMotionRuntime::Get().serial;
 if(!option || std::strcmp(option,"1") || !temporalConsumed || !meta.complete ||
    !fb->iosSceneScaled || fb->GetBuffers()->GetSceneSamples()!=VK_SAMPLE_COUNT_1_BIT ||
    hw_postprocess.customShaders.HasEnabled("scene") || hw_postprocess.customShaders.HasEnabled("screen")) {
  framegenPreviousSerial=0;return false;
 }
 if(meta.reset || !serial || framegenPreviousSerial==UINT64_MAX || serial!=framegenPreviousSerial+1)
  framegenPreviousSerial=0;
 framegenIndex=1-framegenIndex;
 EnsureFramegenTexture(framegenSnapshot);
 EnsureFramegenTexture(framegenClean[framegenIndex]);
 EnsureFramegenTexture(framegenComposite);
 const int savedPipeline=mCurrentPipelineImage;
 CopyFramegenImage(fb->GetBuffers()->PipelineImage[savedPipeline],framegenSnapshot);
 VkPPRenderState state(fb);
 hw_postprocess.Pass2(&state,fixedcm,flash,width,height);
 CopyFramegenImage(fb->GetBuffers()->PipelineImage[mCurrentPipelineImage],framegenClean[framegenIndex]);
 // Restore pre-weapon HDR and pipeline index. Caller follows the original weapon
 // callback and Pass2 unchanged, so real-frame output keeps its prior semantics.
 mCurrentPipelineImage=savedPipeline;
 CopyFramegenImage(framegenSnapshot,fb->GetBuffers()->PipelineImage[savedPipeline]);
 framegenCaptured=true;framegenSerial=serial;
 return true;
}

void VkPostprocess::CaptureFramegenComposite()
{
 if(!framegenCaptured)return;
 // Called AFTER Draw2D, BEFORE twod->Clear: captures weapons, HUD and touch UI
 // exactly as the real frame. No stale HUD replay or independently tonemapped UI.
 if(framegenSerial!=SelacoMotionRuntime::Get().serial){framegenPreviousSerial=0;framegenCaptured=false;return;}
 CopyFramegenImage(fb->GetBuffers()->PipelineImage[mCurrentPipelineImage],framegenComposite);
 framegenPairReady=framegenPreviousSerial && framegenSerial==framegenPreviousSerial+1;
 framegenPreviousSerial=framegenSerial;
 framegenCaptured=false;
}

'''
edit(b+'vulkan/renderer/vk_postprocess.cpp',anchor,body+anchor)
p=root/(b+'vulkan/system/vk_renderdevice.cpp');s=p.read_text()
a=s.index('void VulkanRenderDevice::Update()');z=s.index('void VulkanRenderDevice::OnApplicationActivated',a)
part=s[a:z];assert part.count('\tDraw2D();\n\ttwod->Clear();')==1
edits[p]=s[:a]+part.replace('\tDraw2D();\n\ttwod->Clear();','\tDraw2D();\n\tGetPostprocess()->CaptureFramegenComposite();\n\ttwod->Clear();')+s[z:]
for p,s in edits.items():p.write_text(s)
print('Clean/full framegen capture patched; no interpolation or paired-present caller enabled')

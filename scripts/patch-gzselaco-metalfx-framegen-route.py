#!/usr/bin/env python3
"""Opt-in GPU interpolation route. Apply after composition and paired presentation."""
from pathlib import Path
import sys,shutil
root=Path(sys.argv[1]);edits={}
def edit(rel,old,new):
 p=root/rel;s=edits.get(p,p.read_text());assert s.count(old)==1,(rel,old[:65]);edits[p]=s.replace(old,new)
b='src/common/rendering/vulkan/'
edit(b+'renderer/vk_postprocess.h','#include "common/platform/ios/i_metalfx_backend.h"','#include "common/platform/ios/i_metalfx_backend.h"\n#include "common/platform/ios/i_temporal_present_pacer.h"')
edit(b+'renderer/vk_postprocess.h','\tvoid CaptureFramegenComposite();','\tvoid CaptureFramegenComposite();\n\tvoid ProcessFramegen();')
edit(b+'renderer/vk_postprocess.h','    VkTextureImage framegenSnapshot,framegenClean[2],framegenComposite;', '''    VkTextureImage framegenSnapshot,framegenClean[2],framegenComposite,framegenGenerated;
    IOSMetalFXBackend* iosFramegen=nullptr;
    IOSTemporalPresentPacer framegenPacer;
    uint64_t fgLastTime=0,fgLastSerial=0,fgDrainEpoch=0,fgGeneration=0;
    float fgNear=0,fgFar=0,fgFov=0;
    unsigned fgReported=0;
    void FramegenDiagnostic(unsigned bit,const char* message);''')
edit(b+'renderer/vk_postprocess.cpp','    IOSMetalFXBackendDestroy(iosMetalFX);','    IOSMetalFXBackendDestroy(iosMetalFX);\n    IOSMetalFXBackendDestroy(iosFramegen);')
edit(b+'renderer/vk_postprocess.cpp','    IOSMetalFXBackendRetire(iosMetalFX);','    IOSMetalFXBackendRetire(iosMetalFX);\n    IOSMetalFXBackendRetire(iosFramegen);')
edit(b+'renderer/vk_postprocess.cpp','#include <cstring>','#include <cstring>\n#include <cmath>\n#include "printf.h"')
body=r'''EXTERN_CVAR(Bool, vk_hdr)

void VkPostprocess::FramegenDiagnostic(unsigned bit,const char* message)
{
 if(!(fgReported&bit)){fgReported|=bit;Printf("Selaco MetalFX framegen: %s\n",message);}
}

void VkPostprocess::ProcessFramegen()
{
#if defined(__APPLE__) && TARGET_OS_IPHONE
 auto manager=fb->GetFramebufferManager();auto commands=fb->GetCommands();
 const uint64_t epoch=commands->PairDrainEpoch(),generation=manager->SwapChainGeneration();
 // Generation changes follow swapchain-rebuild drain; exceptional epoch follows
 // pair fence retirement/device drain. Neither is proof of visible presentation.
 if(epoch!=fgDrainEpoch || generation!=fgGeneration){
  framegenPacer.ResetAfterDrain();fgDrainEpoch=epoch;fgGeneration=generation;
  fgLastTime=0;fgLastSerial=0;
 }
 for(const auto& timing:manager->SwapChain->CollectPresentTimings())
  framegenPacer.Retire(timing.presentID,timing.actualPresentTime);
 const char* option=std::getenv("SELACO_IOS_METALFX_FRAMEGEN");
 if(!option || std::strcmp(option,"1")){fgLastTime=0;fgLastSerial=0;return;}
 if(vk_hdr){fgLastTime=0;fgLastSerial=0;FramegenDiagnostic(512,"not generating: HDR/EDR interpolation color contract is not validated");return;}
 const auto meta=SelacoMotionMetadata();const auto serial=SelacoMotionRuntime::Get().serial;
 const uint64_t now=IOSMetalFXPresentationTimeNS();
 if(!temporalConsumed || !meta.complete || !meta.projectionValid || !framegenSerial || framegenSerial!=serial ||
    !framegenClean[framegenIndex].Image || !framegenComposite.Image){
  fgLastTime=0;fgLastSerial=0;
  FramegenDiagnostic(1,"not generating: clean capture/motion/projection unavailable (custom scene/screen effects excluded)");return;
 }
 const bool stable=fgLastSerial && serial==fgLastSerial+1 && now>fgLastTime &&
  meta.nearPlane==fgNear && meta.farPlane==fgFar && std::fabs(meta.verticalFovDegrees-fgFov)<0.0001f;
 const uint64_t delta=now>fgLastTime?now-fgLastTime:0;
 fgLastTime=now;fgLastSerial=serial;fgNear=meta.nearPlane;fgFar=meta.farPlane;fgFov=meta.verticalFovDegrees;
 if(!stable || !framegenPairReady || meta.reset || !delta || delta>100000000){
  FramegenDiagnostic(2,"waiting for consecutive stable clean/projection history");return;
 }
 const uint64_t refresh=manager->SwapChain->TimedPresentRefreshNS();
 if(!manager->ReadyForPair() || !refresh || refresh>11111112){
  FramegenDiagnostic(4,"not generating: FIFO display timing with 90+ Hz refresh is required");return;
 }
 IOSTemporalPresentPacer::Pair pair;
 if(!framegenPacer.Reserve(now,refresh,delta,true,true,pair)){
  FramegenDiagnostic(8,"waiting for presentation feedback or suitable real-frame cadence (45+ FPS)");return;
 }
 EnsureFramegenTexture(framegenGenerated);
 auto buffers=fb->GetBuffers();auto& current=framegenClean[framegenIndex];auto& previous=framegenClean[1-framegenIndex];
 if(!previous.Image || !buffers->SceneDepthStencil.DepthOnlyView || !buffers->SceneMotionDiagnostic.Image || current.Image->width!=previous.Image->width || current.Image->height!=previous.Image->height){
  framegenPacer.CancelUnsubmitted(pair);return;
 }
 fb->GetRenderState()->EndRenderPass();auto cmd=commands->GetDrawCommands();
 VkImageTransition().AddImage(&current,VK_IMAGE_LAYOUT_GENERAL,false)
  .AddImage(&previous,VK_IMAGE_LAYOUT_GENERAL,false).AddImage(&framegenComposite,VK_IMAGE_LAYOUT_GENERAL,false)
  .AddImage(&framegenGenerated,VK_IMAGE_LAYOUT_GENERAL,true)
  .AddImage(&buffers->SceneDepthStencil,VK_IMAGE_LAYOUT_GENERAL,false)
  .AddImage(&buffers->SceneMotionDiagnostic,VK_IMAGE_LAYOUT_GENERAL,false).Execute(cmd);
 IOSMetalFXVkInterpolationFrame f{};
 f.color=current.Image->image;f.previousColor=previous.Image->image;f.compositedColor=framegenComposite.Image->image;
 f.output=framegenGenerated.Image->image;f.depth=buffers->SceneDepthStencil.DepthOnlyView->view;
 f.motion=buffers->SceneMotionDiagnostic.Image->image;
 f.x=framegenInputRect.left;f.y=framegenInputRect.top;f.width=framegenInputRect.width;f.height=framegenInputRect.height;
 f.outputWidth=buffers->GetWidth();f.outputHeight=buffers->GetHeight();
 f.jitterX=meta.jitterX;f.jitterY=meta.jitterY;f.reset=false;
 // Local certification applies only to this split clean pair, not unsplit output.
 f.completeMotion=meta.complete;f.framegenComplete=true;f.cleanScenePair=true;
 f.previousFrameValid=true;f.presentationReserved=true;f.matchedComposition=true;
 f.currentFrameId=serial;f.previousFrameId=serial-1;f.deltaTime=float(double(delta)*1e-9);
 f.nearPlane=meta.nearPlane;f.farPlane=meta.farPlane;f.verticalFovDegrees=meta.verticalFovDegrees;
 f.user=fb;f.flushProducer=[](void*p){static_cast<VulkanRenderDevice*>(p)->GetCommands()->FlushCommands(false);};
 if(!IOSMetalFXBackendInterpolate(iosFramegen,fb->device.get(),f)){
  framegenPacer.CancelUnsubmitted(pair);FramegenDiagnostic(16,"native interpolation unavailable or input validation rejected");return;
 }
 FramegenDiagnostic(32,"native interpolation submitted; visibility requires presentation feedback");
 if(IOSMetalFXPresentationTimeNS()>=pair.generatedNS){
  framegenPacer.CancelUnsubmitted(pair);FramegenDiagnostic(64,"generated deadline missed; presenting real frame only");return;
 }
 const int savedPipeline=mCurrentPipelineImage;
 auto result=commands->PresentIntermediate([&]{
  CopyFramegenImage(framegenGenerated,buffers->PipelineImage[savedPipeline]);
  mCurrentPipelineImage=savedPipeline;
  DrawPresentTexture(fb->mOutputLetterbox,true,false);
  // Same-queue ordering: present draw reads generated before restoring real data.
  CopyFramegenImage(framegenComposite,buffers->PipelineImage[savedPipeline]);
 },pair.generatedNS,pair.generatedID,pair.realNS,pair.realID);
 mCurrentPipelineImage=savedPipeline;
 if(result==VkCommandBufferManager::PairSubmitResult::Rejected)framegenPacer.CancelUnsubmitted(pair);
 else {
  framegenPacer.MarkSubmitted(pair);
  if(result==VkCommandBufferManager::PairSubmitResult::Submitted)
   FramegenDiagnostic(128,"first timed generated/real pair queued; not proof of visible frames");
  else FramegenDiagnostic(256,"pair invalidated; holding reservation until exceptional drain completes");
 }
#endif
}

'''
edit(b+'renderer/vk_postprocess.cpp','void VkPostprocess::BlitSceneToPostprocess()',body+'void VkPostprocess::BlitSceneToPostprocess()')
edit(b+'system/vk_renderdevice.cpp','\tGetPostprocess()->CaptureFramegenComposite();','\tGetPostprocess()->CaptureFramegenComposite();\n\tGetPostprocess()->ProcessFramegen();')
for p,s in edits.items():p.write_text(s)
shutil.copyfile(Path(__file__).resolve().parents[1]/'overlays/gzselaco-ios/i_temporal_present_pacer.h',root/'src/common/platform/ios/i_temporal_present_pacer.h')
print('Opt-in framegen GPU->Vulkan pair route patched; defaults unchanged')

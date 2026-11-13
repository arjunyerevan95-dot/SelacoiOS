#!/usr/bin/env python3
"""Apply after framegen-route: reject before duplicate GPU work, bounded runtime receipts."""
from pathlib import Path
import sys
root=Path(sys.argv[1]); edits={}
def edit(rel,old,new):
 p=root/rel;s=edits.get(p,p.read_text());assert s.count(old)==1,(rel,old[:90]);edits[p]=s.replace(old,new)
b='src/common/rendering/vulkan/renderer/'
edit(b+'vk_postprocess.h','    unsigned fgReported=0;', '''    unsigned fgReported=0;
    uint64_t fgRenderClock=0,fgRenderDelta=0,fgSummaryClock=0;
    unsigned fgCadenceGood=0,fgSummaries=0;
    struct FGCounts { unsigned rendered=0,temporal=0,motion=0,projection=0,customScene=0,customScreen=0,
        captures=0,encoded=0,queued=0,feedback=0,hdrBlocked=0,timingBlocked=0,pendingBlocked=0,cadenceBlocked=0; } fgCounts;
    void PollFramegenFeedback();
    bool AdmitFramegenCapture();
    void CountFramegenRender();''')
start=' auto manager=fb->GetFramebufferManager();auto commands=fb->GetCommands();\n const uint64_t epoch=commands->PairDrainEpoch(),generation=manager->SwapChainGeneration();'
end=' for(const auto& timing:manager->SwapChain->CollectPresentTimings())\n  framegenPacer.Retire(timing.presentID,timing.actualPresentTime);'
p=root/(b+'vk_postprocess.cpp');s=p.read_text();a=s.index(start,s.index('void VkPostprocess::ProcessFramegen()'));z=s.index(end,a)+len(end);poll=s[a:z]
poll=poll.replace('fgLastTime=0;fgLastSerial=0;','fgLastTime=0;fgLastSerial=0;framegenPreviousSerial=0;fgCadenceGood=0;fgRenderClock=0;')
poll=poll.replace('  framegenPacer.Retire(timing.presentID,timing.actualPresentTime);','  if(framegenPacer.Retire(timing.presentID,timing.actualPresentTime)) ++fgCounts.feedback;')
edit(b+'vk_postprocess.cpp',s[a:z],''' PollFramegenFeedback();
 CountFramegenRender();
 auto manager=fb->GetFramebufferManager();auto commands=fb->GetCommands();''')
body=r'''void VkPostprocess::PollFramegenFeedback()
{
#if defined(__APPLE__) && TARGET_OS_IPHONE
POLL
#endif
}

bool VkPostprocess::AdmitFramegenCapture()
{
#if defined(__APPLE__) && TARGET_OS_IPHONE
 // No texture allocation, copying or duplicate Pass2 before cheap admission.
 PollFramegenFeedback();
 auto manager=fb->GetFramebufferManager();
 const auto refresh=manager->SwapChain->TimedPresentRefreshNS();
 if(vk_hdr){++fgCounts.hdrBlocked;return false;}
 if(!manager->ReadyForPair() || refresh<4000000 || refresh>11111112){++fgCounts.timingBlocked;return false;}
 if(framegenPacer.HasPending()){++fgCounts.pendingBlocked;return false;}
 // Measured on EVERY renderer Update, including frames with no capture. Recovery
 // cannot depend on doing the expensive work that admission is trying to avoid.
 if(fgCadenceGood<2 || fgRenderDelta<refresh*3/2 || fgRenderDelta>refresh*5/2){++fgCounts.cadenceBlocked;return false;}
 return true;
#else
 return false;
#endif
}

void VkPostprocess::CountFramegenRender()
{
#if defined(__APPLE__) && TARGET_OS_IPHONE
 const uint64_t now=IOSMetalFXPresentationTimeNS();
 fgRenderDelta=fgRenderClock && now>fgRenderClock ? now-fgRenderClock : 0;
 fgRenderClock=now;
 const auto refresh=fb->GetFramebufferManager()->SwapChain->TimedPresentRefreshNS();
 if(refresh>=4000000 && refresh<=11111112 && fgRenderDelta>=refresh*3/2 && fgRenderDelta<=refresh*5/2){if(fgCadenceGood<2)++fgCadenceGood;}
 else fgCadenceGood=0;
 const char* option=std::getenv("SELACO_IOS_METALFX_FRAMEGEN");
 if(!option || std::strcmp(option,"1")){fgCounts={};fgSummaryClock=now;return;}
 const auto meta=SelacoMotionMetadata();
 ++fgCounts.rendered;fgCounts.temporal+=temporalConsumed;fgCounts.motion+=meta.complete;fgCounts.projection+=meta.projectionValid;
 if(!fgSummaryClock)fgSummaryClock=now;
 if(now>fgSummaryClock && now-fgSummaryClock>=2000000000ULL){
  if(fgSummaries<20){
   ++fgSummaries;
   Printf("Selaco MetalFX FG summary %u: renderer frames=%u cadence=%.1f/s (NOT displayed FPS); temporal=%u motion=%u projection=%u customScene=%u customScreen=%u captures=%u encoded=%u queuedPairs=%u realPairFeedback=%u blockedHDR=%u blockedTiming=%u blockedPending=%u blockedCadence=%u\n",
    fgSummaries,fgCounts.rendered,double(fgCounts.rendered)*1e9/double(now-fgSummaryClock),
    fgCounts.temporal,fgCounts.motion,fgCounts.projection,fgCounts.customScene,fgCounts.customScreen,
    fgCounts.captures,fgCounts.encoded,fgCounts.queued,fgCounts.feedback,
    fgCounts.hdrBlocked,fgCounts.timingBlocked,fgCounts.pendingBlocked,fgCounts.cadenceBlocked);
  }
  fgCounts={};fgSummaryClock=now;
 }
#endif
}

'''.replace('POLL',poll)
edit(b+'vk_postprocess.cpp','void VkPostprocess::FramegenDiagnostic(unsigned bit,const char* message)',body+'void VkPostprocess::FramegenDiagnostic(unsigned bit,const char* message)')
# EXTERN must precede CaptureFramegenClean, which is earlier than route helper definitions.
edit(b+'vk_postprocess.cpp','EXTERN_CVAR(Bool, vk_hdr)\n','')
edit(b+'vk_postprocess.cpp','void VkPostprocess::EnsureFramegenTexture(VkTextureImage& image)','EXTERN_CVAR(Bool, vk_hdr)\n\nvoid VkPostprocess::EnsureFramegenTexture(VkTextureImage& image)')
edit(b+'vk_postprocess.cpp',' const auto serial=SelacoMotionRuntime::Get().serial;\n if(!option', ''' const auto serial=SelacoMotionRuntime::Get().serial;
 if(!option || std::strcmp(option,"1") || !AdmitFramegenCapture()){
  framegenPreviousSerial=0;framegenSerial=0;fgLastTime=0;fgLastSerial=0;return false;
 }
 const bool customScene=hw_postprocess.customShaders.HasEnabled("scene");
 const bool customScreen=hw_postprocess.customShaders.HasEnabled("screen");
 fgCounts.customScene+=customScene;fgCounts.customScreen+=customScreen;
 if(!option''')
edit(b+'vk_postprocess.cpp','    hw_postprocess.customShaders.HasEnabled("scene") || hw_postprocess.customShaders.HasEnabled("screen")) {','    customScene || customScreen) {')
edit(b+'vk_postprocess.cpp',' framegenCaptured=true;framegenSerial=serial;',' framegenCaptured=true;framegenSerial=serial;++fgCounts.captures;')
edit(b+'vk_postprocess.cpp',' FramegenDiagnostic(32,"native interpolation submitted; visibility requires presentation feedback");',' ++fgCounts.encoded;\n FramegenDiagnostic(32,"native interpolation submitted; visibility requires presentation feedback");')
edit(b+'vk_postprocess.cpp','  if(result==VkCommandBufferManager::PairSubmitResult::Submitted)\n   FramegenDiagnostic(128,"first timed generated/real pair queued; not proof of visible frames");','  if(result==VkCommandBufferManager::PairSubmitResult::Submitted){\n   ++fgCounts.queued;FramegenDiagnostic(128,"first timed generated/real pair queued; not proof of visible frames");\n  }')
for p,s in edits.items():p.write_text(s)
print('Early FG admission and bounded renderer-cadence receipts patched; two clean captures still required')

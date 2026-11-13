#!/usr/bin/env python3
"""Materialized source ordering checks; not renderer/device validation."""
from pathlib import Path
import sys
r=Path(sys.argv[1]);s=(r/'src/common/rendering/vulkan/renderer/vk_postprocess.cpp').read_text()
p=s.split('void VkPostprocess::ProcessFramegen()',1)[1].split('void VkPostprocess::BlitSceneToPostprocess()',1)[0]
for gate in ['!meta.complete','!meta.projectionValid','!framegenPairReady','meta.reset','delta>100000000','if(vk_hdr)','!manager->ReadyForPair()']:
 assert gate in p,gate
assert p.index('PairDrainEpoch()')<p.index('std::getenv')
assert p.index('CollectPresentTimings()')<p.index('std::getenv')
assert 'IOSMetalFXPresentationTimeNS()' in p and 'I_GetTimeNS' not in p
assert p.index('Reserve(')<p.index('IOSMetalFXBackendInterpolate(')<p.index('PresentIntermediate(')
callback=p.split('auto result=commands->PresentIntermediate([&]{',1)[1].split('},pair.generatedNS',1)[0]
assert callback.index('CopyFramegenImage(framegenGenerated')<callback.index('DrawPresentTexture(')<callback.index('CopyFramegenImage(framegenComposite')
assert 'PairSubmitResult::Rejected)framegenPacer.CancelUnsubmitted(pair)' in p
assert 'framegenPacer.MarkSubmitted(pair)' in p
u=(r/'src/common/rendering/vulkan/system/vk_renderdevice.cpp').read_text().split('void VulkanRenderDevice::Update()',1)[1].split('void VulkanRenderDevice::OnApplicationActivated',1)[0]
assert u.index('Draw2D();')<u.index('CaptureFramegenComposite();')<u.index('ProcessFramegen();')<u.index('twod->Clear();')
print('framegen route/capture/restore/gates/presentation contract PASS')

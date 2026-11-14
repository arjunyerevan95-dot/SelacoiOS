#!/usr/bin/env python3
"""Admission ordering/source contracts plus skipped-capture recovery model."""
from pathlib import Path
import sys
p=Path(sys.argv[1])/'src/common/rendering/vulkan/renderer/vk_postprocess.cpp'
s=p.read_text()
clean=s[s.index('bool VkPostprocess::CaptureFramegenClean'):s.index('void VkPostprocess::CaptureFramegenComposite')]
assert clean.index('AdmitFramegenCapture()')<clean.index('EnsureFramegenTexture(')<clean.index('hw_postprocess.Pass2(')
assert 'framegenPreviousSerial=0;framegenSerial=0;fgLastTime=0;fgLastSerial=0;return false;' in clean
admit=s[s.index('bool VkPostprocess::AdmitFramegenCapture'):s.index('void VkPostprocess::CountFramegenRender')]
for guard in ['if(vk_hdr)','!manager->ReadyForPair()','refresh>16666668','framegenPacer.HasPending()','fgCadenceGood<2']:
 assert guard in admit,guard
process=s[s.index('void VkPostprocess::ProcessFramegen()'):s.index('void VkPostprocess::BlitSceneToPostprocess()')]
assert process.index('const char* option=')<process.index('CountFramegenRender();')<process.index('!temporalConsumed')
assert 'if(framegenPacer.HasPending())PollFramegenFeedback();' in process
assert process.index('fgRenderClock=0;fgCadenceGood=0;return;') < process.index('CountFramegenRender();')
assert '++fgCounts.encoded;' in process and '++fgCounts.queued;' in process
count=s[s.index('void VkPostprocess::CountFramegenRender()'):s.index('void VkPostprocess::FramegenDiagnostic')]
assert 'fgRenderClock=now' in count and 'fgSummaries<20' in count and '2000000000ULL' in count
assert 'NOT displayed FPS' in count
assert 'if(framegenPacer.Retire(timing.presentID,timing.actualPresentTime)) ++fgCounts.feedback;' in s
assert 'framegenPairReady=framegenPreviousSerial && framegenSerial==framegenPreviousSerial+1;' in s
# Capture skipping never stops real-frame cadence sampling. Slow production rejects;
# two cheap good frames recover eligibility, followed by two clean-history frames.
refresh=8333333; good=0; previous=0; captures=[]; pairs=[]
for serial,delta in enumerate([70000000,70000000,16666666,16666666,16666666,16666666],1):
 admitted=good>=2
 if admitted:
  captures.append(serial)
  if previous and serial==previous+1:pairs.append(serial)
  previous=serial
 else:previous=0
 good=min(2,good+1) if refresh*3//2<=delta<=40000000 else 0
assert captures==[5,6] and pairs==[6],(captures,pairs)
print('PASS: cheap admission before GPU capture; independent cadence recovery; two-capture warmup; bounded truthful counters')

from pathlib import Path
import sys
r=Path(sys.argv[1]);s=(r/'src/common/rendering/vulkan/renderer/vk_postprocess.cpp').read_text()
p=s[s.index('void VkPostprocess::ProcessFramegen()'):s.index('void VkPostprocess::BlitSceneToPostprocess()')]
assert p.index('SelacoCompare::Render();')<p.index('if(!option')
assert 'if(framegenPacer.HasPending())PollFramegenFeedback();' in p
assert s.count('SelacoCompare::Encode();')==1
assert 'std::getenv("SELACO_IOS_METALFX_FRAMEGEN")' not in s
assert '++fgCounts.encoded;SelacoCompare::Encode();' in p
print('PASS compare counters: renders counted off/on; encoded not presented; pending retirement intact')

b=(r/'src/common/platform/ios/i_metalfx_backend.mm').read_text()
assert 'const char* opt=SelacoCompare::Enabled()?"1":"0";' in b

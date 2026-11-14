#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(sys.argv[1]);p=root/'src/common/rendering/vulkan/renderer/vk_postprocess.cpp';s=p.read_text()
s='#include "common/platform/ios/i_framegen_compare.h"\n'+s
old='void VkPostprocess::ProcessFramegen()\n{'
assert s.count(old)==1
s=s.replace(old,old+'\n SelacoCompare::Render();')
old='const char* option=std::getenv("SELACO_IOS_METALFX_FRAMEGEN");'
assert s.count(old)>=2
s=s.replace(old,'const char* option=SelacoCompare::Enabled()?"1":"0";')
assert s.count('++fgCounts.encoded;')==1
s=s.replace('++fgCounts.encoded;','++fgCounts.encoded;SelacoCompare::Encode();')
p.write_text(s)
print('PASS: compare overlay counts engine renders, never display-link ticks; FG counts encoded only')

p=root/'src/common/platform/ios/i_metalfx_backend.mm';s=p.read_text()
s='#include "i_framegen_compare.h"\n'+s
old='const char* opt=std::getenv("SELACO_IOS_METALFX_FRAMEGEN");'
assert s.count(old)==1
s=s.replace(old,'const char* opt=SelacoCompare::Enabled()?"1":"0";');p.write_text(s)

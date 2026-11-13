#!/usr/bin/env python3
"""Opt-in iOS sole FPS cap ahead of simulation/input, not after rendered work.
No extra event pump, tick-rate change, queue-depth change or fence removal.
"""
from pathlib import Path
import sys
r=Path(sys.argv[1]); edits={}
def edit(p,old,new):
 s=edits.get(p,(r/p).read_text()); assert s.count(old)==1,(p,old[:80]);edits[p]=s.replace(old,new)
edit('src/common/rendering/v_video.h','\tvoid FPSLimit();','\tvoid FPSLimit();\n\tvirtual void LimitBeforeInput() {}')
edit('src/d_main.cpp','\t\t\t// frame syncronous IO operations','\t\t\tif (screen) screen->LimitBeforeInput();\n\n\t\t\t// frame syncronous IO operations')
edit('src/common/rendering/vulkan/system/vk_renderdevice.h','\tbool GetVSync() { return mVSync; }','''\tvoid LimitBeforeInput() override;
\tbool ConsumeEarlyLimit() { bool used = mEarlyLimited; mEarlyLimited = false; return used; }
\tbool mEarlyLimited = false;
\tbool GetVSync() { return mVSync; }''')
p='src/common/rendering/vulkan/system/vk_renderdevice.cpp'
edit(p,'#include "vk_renderdevice.h"','''#include "vk_renderdevice.h"
#include <cstdlib>
#include <cstring>
#if defined(__APPLE__)
#include <TargetConditionals.h>
#endif''')
edit(p,'void VulkanRenderDevice::Update()','''void VulkanRenderDevice::LimitBeforeInput()
{
\tmEarlyLimited = false;
#if defined(__APPLE__) && TARGET_OS_IPHONE
\tconst char* enabled = std::getenv("SELACO_IOS_EARLY_LIMIT");
\tif (enabled && std::strcmp(enabled, "1") == 0 && !GetVSync())
\t{
\t\t// Existing limiter retains its menu/maxfps/capfps behavior. This wait
\t\t// now precedes I_SetFrameTime, simulation and final pre-render input.
\t\textern glcycle_t FPSWait;
\t\tFPSWait.Reset(); FPSWait.Clock();
\t\tFPSLimit();
\t\tFPSWait.Unclock();
\t\tmEarlyLimited = true;
\t}
#endif
}

void VulkanRenderDevice::Update()''')
p='src/common/rendering/vulkan/system/vk_commandbuffer.cpp'
edit(p,'\t\tif (!fb->GetVSync()) {','\t\tconst bool alreadyLimited = fb->ConsumeEarlyLimit();\n\t\tif (!fb->GetVSync() && !alreadyLimited) {')
for p,s in edits.items():(r/p).write_text(s)
print('Opt-in sole early FPS limiter patched; device latency remains unmeasured')

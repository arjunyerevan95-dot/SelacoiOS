#!/usr/bin/env python3
"""Retire old swapchain resources safely; signal presentation per acquired image."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
def edit(rel,old,new):
 p=root/rel;s=p.read_text();assert s.count(old)==1,(rel,old[:50]);p.write_text(s.replace(old,new))
p='src/common/rendering/vulkan/textures/vk_framebuffer.h'
edit(p,'#include <map>','#include <map>\n#include <vector>')
edit(p,'\tstd::unique_ptr<VulkanSemaphore> RenderFinishedSemaphore;', '''\t// Reacquiring an image proves its preceding presentation wait has completed.
\tstd::vector<std::unique_ptr<VulkanSemaphore>> RenderFinishedSemaphores;
\tVulkanSemaphore *GetRenderFinishedSemaphore() {
\t\treturn RenderFinishedSemaphores.at(PresentImageIndex).get();
\t}''')
p='src/common/rendering/vulkan/textures/vk_framebuffer.cpp'
edit(p,'#include "vk_framebuffer.h"','#include "vk_framebuffer.h"\n#include "printf.h"')
edit(p,'''\tRenderFinishedSemaphore = SemaphoreBuilder()
\t\t.DebugName("RenderFinishedSemaphore")
\t\t.Create(fb->device.get());''','\t// Presentation semaphores are allocated per swapchain image below.')
edit(p,'\t\tFramebuffers.clear();','''\t\t// A graphics fence alone does not retire a queued presentation operation.
\t\t// Rebuild only after presentation and rendering have both drained.
\t\tif (vkDeviceWaitIdle(fb->device->device) != VK_SUCCESS)
\t\t\tVulkanError("iOS swapchain retirement wait failed");
\t\tFramebuffers.clear();
\t\tRenderFinishedSemaphores.clear();''')
anchor='\t\tSwapChain->Create(CurrentWidth, CurrentHeight, CurrentVSync ? 2 : 3, CurrentVSync, CurrentHdr, CurrentExclusiveFullscreen);'
edit(p,anchor,anchor+'''
\t\tfor (int i = 0; i < SwapChain->ImageCount(); ++i)
\t\t\tRenderFinishedSemaphores.push_back(SemaphoreBuilder()
\t\t\t\t.DebugName("ImageRenderFinishedSemaphore").Create(fb->device.get()));
\t\tPrintf("iOS swapchain rebuilt: %dx%d vsync=%d images=%d per-image-present-sync\\n",
\t\t\tCurrentWidth, CurrentHeight, CurrentVSync, SwapChain->ImageCount());''')
edit(p,'SwapChain->QueuePresent(PresentImageIndex, RenderFinishedSemaphore.get());','SwapChain->QueuePresent(PresentImageIndex, GetRenderFinishedSemaphore());')
edit('src/common/rendering/vulkan/system/vk_commandbuffer.cpp','submit.AddSignal(fb->GetFramebufferManager()->RenderFinishedSemaphore.get());','submit.AddSignal(fb->GetFramebufferManager()->GetRenderFinishedSemaphore());')

# iOS/MoltenVK's immediate-present path has exhibited blank/flashing frames.
# Prefer supported mailbox; retain FIFO safely when mailbox is unavailable.
p='libraries/ZVulkan/src/vulkanswapchain.cpp'
edit(p,'#include "vulkanswapchain.h"', '#include "vulkanswapchain.h"\n#include <cstdio>\n#if defined(__APPLE__)\n#include <TargetConditionals.h>\n#endif')
edit(p,'\tSelectFormat(caps, hdr);', '''
#if defined(__APPLE__) && TARGET_OS_IPHONE
\tif (!vsync) presentMode = supportsMailbox ? VK_PRESENT_MODE_MAILBOX_KHR : VK_PRESENT_MODE_FIFO_KHR;
\tstd::fprintf(stderr, "Selaco iOS presentation: requestedVSync=%d selectedMode=%d mailbox=%d immediate=%d%s\\n",
\t\tint(vsync), int(presentMode), int(supportsMailbox), int(supportsImmediate),
\t\t!vsync && !supportsMailbox ? " FIFO safety fallback (not uncapped)" : "");
#endif
\tSelectFormat(caps, hdr);''')
# Experimental stack is intentionally excluded from ordinary controls builds.
# This hook is shared by the native app build and source materializer, so they
# cannot silently validate a different source tree. Runtime opt-in is separate.
import os, subprocess
if os.environ.get('SELACO_METALFX_EXPERIMENTAL_BUILD') == '1':
    subprocess.run([sys.executable, str(Path(__file__).resolve().parent / 'patch-gzselaco-metalfx-stack.py'), str(root)], check=True)

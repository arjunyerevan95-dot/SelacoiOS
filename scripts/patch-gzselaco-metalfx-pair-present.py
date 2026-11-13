#!/usr/bin/env python3
"""Prepare real Vulkan two-image presentation plumbing; no framegen enablement.
Apply after the experimental stack. Caller must supply valid composed output and
reserve timed presentation before invoking PresentIntermediate. The ordinary
frame remains owned by WaitForCommands and its existing fence retirement.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1]); edits={}
def edit(rel,old,new):
    p=root/rel;s=edits.get(p,p.read_text());assert s.count(old)==1,(rel,old[:70]);edits[p]=s.replace(old,new)
b='src/common/rendering/vulkan/'
edit(b+'textures/vk_framebuffer.h','#include <vector>','#include <vector>\n#include <functional>')
edit(b+'textures/vk_framebuffer.h','\tvoid AcquireImage();\n\tvoid QueuePresent();','''\t// An intermediate generated output and the final real output must not reuse
\t// the same binary acquire semaphore before its GPU wait has completed.
\tvoid AcquireImage(unsigned slot = 0, const std::function<void()>& draw = {});
\tvoid QueuePresent(uint64_t timeNS = 0, uint32_t presentID = 0);
\tVulkanSemaphore* GetImageAvailableSemaphore() {
\t\treturn ActiveAcquireSlot ? PairImageAvailableSemaphore.get() : SwapChainImageAvailableSemaphore.get();
\t}''')
edit(b+'textures/vk_framebuffer.h','\tVulkanRenderDevice* fb = nullptr;','''\tVulkanRenderDevice* fb = nullptr;
\tstd::unique_ptr<VulkanSemaphore> PairImageAvailableSemaphore;
\tunsigned ActiveAcquireSlot = 0;''')
edit(b+'textures/vk_framebuffer.cpp','\t// Presentation semaphores are allocated per swapchain image below.','''\tPairImageAvailableSemaphore = SemaphoreBuilder()
\t\t.DebugName("PairImageAvailableSemaphore").Create(fb->device.get());
\t// Presentation semaphores are allocated per swapchain image below.''')
edit(b+'textures/vk_framebuffer.cpp','void VkFramebufferManager::AcquireImage()\n{','''void VkFramebufferManager::AcquireImage(unsigned slot, const std::function<void()>& draw)
{
\tif (slot > 1) VulkanError("Invalid paired acquire semaphore slot");
\tActiveAcquireSlot = slot;''')
edit(b+'textures/vk_framebuffer.cpp','SwapChain->AcquireImage(SwapChainImageAvailableSemaphore.get())','SwapChain->AcquireImage(GetImageAvailableSemaphore())')
edit(b+'textures/vk_framebuffer.cpp','\t\tfb->GetPostprocess()->DrawPresentTexture(fb->mOutputLetterbox, true, false);','''\t\tif (draw) draw();
\t\telse fb->GetPostprocess()->DrawPresentTexture(fb->mOutputLetterbox, true, false);''')
edit(b+'textures/vk_framebuffer.cpp','void VkFramebufferManager::QueuePresent()','void VkFramebufferManager::QueuePresent(uint64_t timeNS, uint32_t presentID)')
edit(b+'textures/vk_framebuffer.cpp','SwapChain->QueuePresent(PresentImageIndex, GetRenderFinishedSemaphore());','SwapChain->QueuePresent(PresentImageIndex, GetRenderFinishedSemaphore(), timeNS, presentID);')
edit(b+'system/vk_commandbuffer.h','#include "zstring.h"','#include "zstring.h"\n#include <functional>')
edit(b+'system/vk_commandbuffer.h','\tvoid BeginFrame();','''\tvoid BeginFrame();
\t// Submit at most one generated output before the usual real-frame present.
\t// draw must record a complete draw into the acquired swapchain image. Caller
\t// retains all output resources until the ordinary WaitForCommands retires.
\t// True means submitted, NOT visible; retire pacing using display feedback.
\tbool PresentIntermediate(const std::function<void()>& draw,
\t\tuint64_t generatedNS, uint32_t generatedID, uint64_t realNS, uint32_t realID);''')
edit(b+'system/vk_commandbuffer.h','\tint mNextSubmit = 0;','''\tint mNextSubmit = 0;
\tbool mIntermediateSubmitted = false;
\tuint64_t mPairedRealNS = 0;
\tuint32_t mPairedRealID = 0;''')
edit(b+'system/vk_commandbuffer.cpp','fb->GetFramebufferManager()->SwapChainImageAvailableSemaphore.get()','fb->GetFramebufferManager()->GetImageAvailableSemaphore()')
edit(b+'system/vk_commandbuffer.cpp','void VkCommandBufferManager::WaitForCommands(bool finish, bool uploadOnly)','''bool VkCommandBufferManager::PresentIntermediate(const std::function<void()>& draw,
\tuint64_t generatedNS, uint32_t generatedID, uint64_t realNS, uint32_t realID)
{
\tauto manager = fb->GetFramebufferManager();
\tif (mIsUploadOnly || mIntermediateSubmitted || !draw || !generatedNS ||
\t\t!generatedID || realNS <= generatedNS || realID <= generatedID ||
\t\t!manager->SwapChain->TimedPresentRefreshNS()) return false;
\tmanager->AcquireImage(0, draw);
\tif (manager->PresentImageIndex == -1) return false;
\t// Keep the submission-chain signal alive for the following real-frame draw.
\tGetDrawCommands(); // Ensure even an empty callback consumes the acquire signal.
\tFlushCommands(true, false, false);
\tmanager->QueuePresent(generatedNS, generatedID);
\tmIntermediateSubmitted = true;
\tmPairedRealNS = realNS;
\tmPairedRealID = realID;
\treturn true;
}

void VkCommandBufferManager::WaitForCommands(bool finish, bool uploadOnly)''')
edit(b+'system/vk_commandbuffer.cpp','\t\tfb->GetFramebufferManager()->AcquireImage();','\t\tfb->GetFramebufferManager()->AcquireImage(mIntermediateSubmitted ? 1 : 0);')
edit(b+'system/vk_commandbuffer.cpp','\t\tfb->GetFramebufferManager()->QueuePresent();','\t\tfb->GetFramebufferManager()->QueuePresent(mPairedRealNS, mPairedRealID);')
edit(b+'system/vk_commandbuffer.cpp','\tDeleteFrameObjects(uploadOnly);\n\tmNextSubmit = 0;','''\tDeleteFrameObjects(uploadOnly);
\tmNextSubmit = 0;
\t// Both acquire semaphore GPU waits are covered by the fences above. Present
\t// semaphores stay per-image; reacquisition still proves their safe reuse.
\tmIntermediateSubmitted = false;
\tmPairedRealNS = 0;
\tmPairedRealID = 0;''')
edit(b+'system/vk_commandbuffer.cpp','void VkCommandBufferManager::WaitForCommands(bool finish, bool uploadOnly)\n{','void VkCommandBufferManager::WaitForCommands(bool finish, bool uploadOnly)\n{\n\tif (mIntermediateSubmitted && (!finish || uploadOnly))\n\t\tVulkanError("Paired presentation must finish before unrelated retirement");')
for p,s in edits.items():p.write_text(s)
print('Paired Vulkan presentation plumbing patched; no framegen caller enabled')

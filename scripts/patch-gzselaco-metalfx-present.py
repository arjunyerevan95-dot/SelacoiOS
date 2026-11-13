#!/usr/bin/env python3
"""Add opt-in Vulkan timed presentation. No competing CAMetalLayer owner.
Apply after patch-gzselaco-metalfx-device.py. Existing QueuePresent callers unchanged.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1]); pending={}
def edit(rel, old, new):
    p=root/rel; s=pending.get(p,p.read_text())
    assert s.count(old)==1,(rel,old[:80])
    pending[p]=s.replace(old,new)
b='libraries/ZVulkan/'
edit(b+'include/zvulkan/vulkanswapchain.h',
    '\tvoid QueuePresent(int imageIndex, VulkanSemaphore* semaphore = nullptr);',
    '''\tvoid QueuePresent(int imageIndex, VulkanSemaphore* semaphore = nullptr, uint64_t desiredTimeNS = 0, uint32_t presentID = 0);
\t// Zero means unsupported/unknown. Frame generation must remain off then.
\tuint64_t TimedPresentRefreshNS() const;
\tstd::vector<VkPastPresentationTimingGOOGLE> CollectPresentTimings() const;''')
edit(b+'src/vulkanswapchain.cpp',
    'void VulkanSwapChain::QueuePresent(int imageIndex, VulkanSemaphore* semaphore)',
    '''uint64_t VulkanSwapChain::TimedPresentRefreshNS() const
{
\tif (lost || swapchain == VK_NULL_HANDLE || presentMode != VK_PRESENT_MODE_FIFO_KHR ||
\t\t!device->SupportsExtension(VK_GOOGLE_DISPLAY_TIMING_EXTENSION_NAME)) return 0;
\tauto query = reinterpret_cast<PFN_vkGetRefreshCycleDurationGOOGLE>(
\t\tvkGetDeviceProcAddr(device->device, "vkGetRefreshCycleDurationGOOGLE"));
\tVkRefreshCycleDurationGOOGLE duration = {};
\treturn query && query(device->device, swapchain, &duration) == VK_SUCCESS ? duration.refreshDuration : 0;
}

std::vector<VkPastPresentationTimingGOOGLE> VulkanSwapChain::CollectPresentTimings() const
{
\tstd::vector<VkPastPresentationTimingGOOGLE> timings;
\tif (!TimedPresentRefreshNS()) return timings;
\tauto query = reinterpret_cast<PFN_vkGetPastPresentationTimingGOOGLE>(
\t\tvkGetDeviceProcAddr(device->device, "vkGetPastPresentationTimingGOOGLE"));
\tuint32_t count = 0;
\tif (!query || query(device->device, swapchain, &count, nullptr) != VK_SUCCESS || !count || count > 256) return timings;
\ttimings.resize(count);
\tVkResult result = query(device->device, swapchain, &count, timings.data());
\tif (result != VK_SUCCESS && result != VK_INCOMPLETE) timings.clear();
\telse timings.resize(count);
\treturn timings;
}

void VulkanSwapChain::QueuePresent(int imageIndex, VulkanSemaphore* semaphore, uint64_t desiredTimeNS, uint32_t presentID)''')
edit(b+'src/vulkanswapchain.cpp',
    '\tVkResult result = vkQueuePresentKHR(device->PresentQueue, &presentInfo);',
    '''\t// desiredTimeNS is the platform monotonic presentation clock, not wall time.
\t// Caller must query TimedPresentRefreshNS and reserve unique IDs before a pair.
\tVkPresentTimeGOOGLE time = { presentID, desiredTimeNS };
\tVkPresentTimesInfoGOOGLE timing = { VK_STRUCTURE_TYPE_PRESENT_TIMES_INFO_GOOGLE };
\tif (desiredTimeNS && presentID && TimedPresentRefreshNS())
\t{
\t\ttiming.swapchainCount = 1;
\t\ttiming.pTimes = &time;
\t\ttiming.pNext = presentInfo.pNext;
\t\tpresentInfo.pNext = &timing;
\t}
\tVkResult result = vkQueuePresentKHR(device->PresentQueue, &presentInfo);''')
edit('src/common/rendering/vulkan/system/vk_renderdevice.cpp',
    '\t\tbuilder.OptionalExtension(VK_KHR_TIMELINE_SEMAPHORE_EXTENSION_NAME);',
    '\t\tbuilder.OptionalExtension(VK_KHR_TIMELINE_SEMAPHORE_EXTENSION_NAME);\n\t\tbuilder.OptionalExtension(VK_GOOGLE_DISPLAY_TIMING_EXTENSION_NAME);')
for p,s in pending.items():p.write_text(s)
print('Optional timed Vulkan presentation patched; framegen callers remain gated')

#!/usr/bin/env python3
"""Focused source-contract check on materialized pair lifecycle, not GPU proof."""
from pathlib import Path
import sys
r=Path(sys.argv[1]);base=r/'src/common/rendering/vulkan'
c=(base/'system/vk_commandbuffer.cpp').read_text()
f=(base/'textures/vk_framebuffer.cpp').read_text()
z=(r/'libraries/ZVulkan/src/vulkanswapchain.cpp').read_text()
method=c.split('VkCommandBufferManager::PairSubmitResult VkCommandBufferManager::PresentIntermediate',1)[1].split('void VkCommandBufferManager::WaitForCommands',1)[0]
assert method.index('ReadyForPair()') < method.index('AcquireImage(0,')
assert 'manager->SwapChainGeneration()==mPairGeneration' in method
assert 'if(manager->PresentImageIndex==-1)return PairSubmitResult::Rejected;' in method
acquired=method.split('if(manager->PresentImageIndex==-1)return PairSubmitResult::Rejected;',1)[1]
assert 'return PairSubmitResult::Rejected' not in acquired
assert acquired.index('FlushCommands(true,false,false)') < acquired.index('QueuePresent(')
assert 'presented!=VK_SUCCESS' in acquired and 'PairSubmitResult::Draining' in acquired
assert 'DrawPresentTexture(fb->mOutputLetterbox,true,false)' in method
retire=c.split('void VkCommandBufferManager::WaitForCommands',1)[1].split('void VkCommandBufferManager::DeleteFrameObjects',1)[0]
assert retire.index('vkWaitForFences') < retire.index('++mPairDrainEpoch')
assert retire.index('vkDeviceWaitIdle') < retire.index('++mPairDrainEpoch')
assert 'SwapChainGeneration()!=mPairGeneration' in retire
assert 'AcquireImage(mIntermediateSubmitted ? 1 : 0)' in retire
assert '++Generation' in f and 'return SwapChain->QueuePresent' in f
present=z.split('VkResult VulkanSwapChain::QueuePresent',1)[1].split('VulkanSurfaceCapabilities VulkanSwapChain::GetSurfaceCapabilities',1)[0]
assert 'return result;' in present and 'return;' not in present
print('paired acquire/present generation and exceptional-drain contracts PASS')

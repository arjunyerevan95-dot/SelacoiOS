from pathlib import Path
import subprocess,sys,tempfile
repo=Path(__file__).resolve().parents[1]
source=Path(sys.argv[1]) if len(sys.argv)>1 else repo/'build/metalfx-candidate-full'
with tempfile.TemporaryDirectory(prefix='selaco-output-') as d:
 root=Path(d)
 for rel in ['src/common/platform/ios/i_engine_renderer_handoff.mm','libraries/ZVulkan/src/vulkanswapchain.cpp']:
  dst=root/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((source/rel).read_bytes())
 subprocess.run([sys.executable,str(repo/'scripts/patch-gzselaco-ios-output-transition.py'),str(root)],check=True)
 s=(root/'libraries/ZVulkan/src/vulkanswapchain.cpp').read_text()
 create=s[s.index('bool VulkanSwapChain::CreateSwapchain'):s.index('int VulkanSwapChain::AcquireImage')]
 hook=create.index('SelacoIOSValidateSwapchainLayer')
 assert create.index('vkDestroySwapchainKHR(device->device, swapChainCreateInfo.oldSwapchain') < hook
 assert create.index('if (result != VK_SUCCESS)') < hook
 assert create.index('return false;',create.index('if (result != VK_SUCCESS)')) < hook
 h=(root/'src/common/platform/ios/i_engine_renderer_handoff.mm').read_text()
 assert h.count('OptionalExtension(VK_EXT_SWAPCHAIN_COLOR_SPACE_EXTENSION_NAME)')==1
 assert 'if (repaired) layer.drawableSize = CGSizeMake(width, height)' in h
 assert 'swapchain_layer_output' in h
 assert 'wantsExtendedDynamicRangeContent =' not in h
print('PASS output transition source contract: successful-create ordering, optional HDR discovery, non-owning layer repair/evidence')


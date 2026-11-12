from pathlib import Path
import tempfile,shutil,subprocess,sys
repo=Path(__file__).resolve().parents[1];base=Path(sys.argv[1])
files=['src/common/rendering/vulkan/textures/vk_framebuffer.h','src/common/rendering/vulkan/textures/vk_framebuffer.cpp','src/common/rendering/vulkan/system/vk_commandbuffer.cpp','src/common/audio/sound/oalsound.cpp','src/common/audio/sound/s_sound.cpp']
with tempfile.TemporaryDirectory() as d:
 for rel in files:
  p=Path(d)/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy(base/rel,p)
 for script in ['patch-gzselaco-present-lifetime.py','patch-gzselaco-audio-diagnostics.py']:
  subprocess.run([sys.executable,str(repo/'scripts'/script),d],check=True)
 h,s,c,a,b=[(Path(d)/f).read_text() for f in files]
 assert s.index('vkDeviceWaitIdle')<s.index('Framebuffers.clear')<s.index('SwapChain->Create')<s.index('SwapChain->ImageCount')
 assert 'RenderFinishedSemaphore.get()' not in s+c
 assert 'RenderFinishedSemaphores.at(PresentImageIndex)' in h
 assert 'GetRenderFinishedSemaphore()' in s and 'GetRenderFinishedSemaphore()' in c
 assert 'count++ < 24' in b and 'iOS OpenAL inactive-state' in a
 print('PASS exact patches, swapchain retirement ordering, per-image semaphore selection, bounded diagnostics')

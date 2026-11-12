#!/usr/bin/env python3
"""Portable patch/geometry regression; does not claim a Vulkan device run."""
from pathlib import Path
import shutil, subprocess, sys, tempfile
repo=Path(__file__).resolve().parents[1]
src=Path(sys.argv[1])
files=['src/common/rendering/vulkan/system/vk_renderdevice.h','src/common/rendering/vulkan/system/vk_renderdevice.cpp','src/common/rendering/vulkan/renderer/vk_postprocess.cpp']
with tempfile.TemporaryDirectory() as d:
 root=Path(d)
 for f in files:
  (root/f).parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src/f,root/f)
 subprocess.run([sys.executable,str(repo/'scripts/patch-gzselaco-scene-scale.py'),d],check=True)
 dev=(root/files[1]).read_text(); pp=(root/files[2]).read_text()
 assert dev.index('gl_multisample = 0') < dev.index('mScreenBuffers->BeginFrame')
 assert 'GetBuffers() == mScreenBuffers.get()' in dev
 assert 'mSceneViewport = iosNativeSceneRect' in dev
 assert pp.index('if (fb->iosSceneScaled)') < pp.index('1, &blit, VK_FILTER_NEAREST')
 assert 'CreateScene(' not in dev # attachment allocator untouched
 assert 'gl_ssao = 0' in dev
 assert 'vid_scalefactor = 1.0f' in dev and 'vid_scalemode = 0' in dev
 assert 'clearColorImage' in pp and 'VK_ACCESS_TRANSFER_WRITE_BIT, VK_ACCESS_TRANSFER_WRITE_BIT' in pp
 for w,h in [(2796,1290),(2556,1179),(1920,1080),(320,200)]:
  for left,top,rw,rh in [(0,0,w,h),(w//8,h//8,w*3//4,h*3//4)]:
   for scale in [.25,.33,.5,.75]:
    x,y=int(left*scale),int(top*scale); sw,sh=max(1,int(rw*scale)),max(1,int(rh*scale))
    assert 0<=x<x+sw<=w and 0<=y<y+sh<=h
    assert left+rw<=w and top+rh<=h
 print('PASS exact source patch, native-pipeline guards, reduced source/destination bounds')

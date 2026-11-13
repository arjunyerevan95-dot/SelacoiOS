#!/usr/bin/env python3
"""Checks emitted source wiring, not compiler/device execution."""
from pathlib import Path
import sys
r=Path(sys.argv[1])
def check(p,*needles):
 s=(r/p).read_text()
 for n in needles: assert n in s,(p,n)
check('src/rendering/hwrenderer/scene/hw_sprites.cpp','SelacoMotionRuntime::Capture(actor,texture,uv,corners)','motionVP.mMotionSpriteInfo={1.f,float(vertexindex),valid?1.f:0.f,0.f}','screen->mViewpoints->Bind(state,di->vpIndex)','Bones/morph history unavailable')
check('src/common/objects/dobject.cpp','SelacoMotionRuntime::Forget(this)')
check('wadsrc/static/shaders/glsl/main.vp','gl_VertexIndex - int(MotionSpriteInfo.y)','PreviousViewMatrix * MotionSpriteCorners[corner]')
check('src/rendering/hwrenderer/scene/hw_drawinfo.cpp','motionViewPath.push_back','SelacoMotionViews::Get().Capture','Portal history unavailable')
check('src/common/rendering/hwrenderer/data/hw_motion_diagnostic.h','framegenComplete=false','inline bool SelacoMotionComplete() { return false; }')
print('PASS source wiring only: prior billboard corners + portal view history; complete=false')

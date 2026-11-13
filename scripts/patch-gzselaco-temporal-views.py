#!/usr/bin/env python3
"""Per-recursion camera history. Portal depth/material completeness remains false."""
from pathlib import Path
import sys
r=Path(sys.argv[1]);e={}
def edit(p,a,b):
 s=e.get(p,(r/p).read_text());assert s.count(a)==1,(p,a[:60],s.count(a));e[p]=s.replace(a,b)
p='src/rendering/hwrenderer/scene/hw_drawinfo.h'
edit(p,'\tint vpIndex;','\tint vpIndex;\n    std::vector<std::uintptr_t> motionViewPath;')
edit(p,'#pragma once','#pragma once\n#include <vector>\n#include <cstdint>')
p='src/rendering/hwrenderer/scene/hw_drawinfo.cpp'
edit(p,'#include "hwrenderer/data/i_motion_sprite_runtime.h"','#include "hwrenderer/data/i_motion_sprite_runtime.h"\n#include "hwrenderer/data/i_motion_view_runtime.h"')
edit(p,'\tdi->StartScene(parentvp, uniforms);','\tdi->StartScene(parentvp, uniforms);\n    di->motionViewPath = parent ? parent->motionViewPath : std::vector<std::uintptr_t>{reinterpret_cast<std::uintptr_t>(lev)};')
edit(p,'\tnew_di->mCurrentPortal = gp;','\tnew_di->mCurrentPortal = gp;\n    new_di->motionViewPath.push_back(reinterpret_cast<std::uintptr_t>(gp->GetSource()));')
edit(p,'\tVPUniforms.CalcDependencies();','''\tVPUniforms.CalcDependencies();
    if(SelacoMotionDiagnostic()) {
        SelacoMotionViews::History::Pair current{VPUniforms.mProjectionMatrix,VPUniforms.mViewMatrix},previous=current;
        const bool valid=SelacoMotionViews::Get().Capture(motionViewPath,current,previous);
        VPUniforms.mPreviousProjectionMatrix=previous.projection;
        VPUniforms.mPreviousViewMatrix=previous.view;
        if(!valid)SelacoMotionRuntime::Reject();
    }''')
# Main SetupView happens before runtime Begin in motion patch: explicitly begin view
# history before it, using steady-clock discontinuity and camera identity.
p='src/rendering/hwrenderer/hw_entrypoint.cpp'
edit(p,'#include "hwrenderer/data/i_motion_sprite_runtime.h"','#include "hwrenderer/data/i_motion_sprite_runtime.h"\n#include "hwrenderer/data/i_motion_view_runtime.h"')
a='\t\tdi->SetupView(RenderState, vp.Pos.X, vp.Pos.Y, vp.Pos.Z, false, false);'
edit(p,a,'''        if(mainview && toscreen && SelacoMotionDiagnostic()) {
            static const void* viewCamera=nullptr;
            static std::chrono::steady_clock::time_point viewTime{};
            const auto now=std::chrono::steady_clock::now();
            SelacoMotionViews::Get().Begin(viewCamera!=camera || std::chrono::duration<double>(now-viewTime).count()>=0.25);
            viewCamera=camera;viewTime=now;
        }
'''+a)
edit(p,'            SelacoMotionRuntime::Commit();','            SelacoMotionRuntime::Commit();\n            SelacoMotionViews::Get().Commit();')
for p,s in e.items():(r/p).write_text(s)
target=r/'src/common/rendering/hwrenderer/data'
overlay=Path(__file__).resolve().parents[1]/'overlays/gzselaco-ios'
(target/'i_motion_view_history.h').write_text((overlay/'i_motion_view_history.h').read_text(encoding='utf-8-sig'))
(target/'i_motion_view_runtime.h').write_text('''#pragma once
#include "i_motion_view_history.h"
#include "matrix.h"
namespace SelacoMotionViews {
using History=SelacoTemporal::ViewHistory<VSMatrix>;
inline History& Get(){static auto* s=new History;return *s;}
}
''')
print('Applied portal recursion camera-history diagnostic; portal depth validity still rejects')

#!/usr/bin/env python3
"""Opt-in supported-frame temporal gate. Apply after consume and all motion patches."""
from pathlib import Path
import sys
r=Path(sys.argv[1]);e={}
def edit(p,a,b):
 s=e.get(p,(r/p).read_text());assert s.count(a)==1,(p,a[:70],s.count(a));e[p]=s.replace(a,b)
p='src/common/rendering/vulkan/renderer/vk_postprocess.cpp'
edit(p,'#include "hwrenderer/data/hw_motion_diagnostic.h"','#include "hwrenderer/data/hw_motion_diagnostic.h"\n#include "hwrenderer/data/i_motion_coverage_runtime.h"\n#include "hwrenderer/data/i_motion_sprite_runtime.h"\n#include "hwrenderer/data/i_motion_view_runtime.h"')
edit(p,'\tmCurrentPipelineImage = 0;\n#if defined(__APPLE__) && TARGET_OS_IPHONE','''\tmCurrentPipelineImage = 0;
#if defined(__APPLE__) && TARGET_OS_IPHONE
    // This is the scene-resolve boundary: all world draw coverage has completed.
    // Real fallback frames never advance MetalFX history.
    const auto candidateMetadata=SelacoMotionMetadata();
    const auto& coverageState=SelacoMotionRuntime::Get();
    const auto coverage=SelacoMotionCoverage::Get().Finalize({
        coverageState.serial,SelacoMotionCoverage::Epoch(),
        unsigned(fb->mSceneViewport.width),unsigned(fb->mSceneViewport.height),
        unsigned(buffers->GetWidth()),unsigned(buffers->GetHeight()),
        SelacoMotionCoverage::Enabled(),
        SelacoMotionCoverage::JitterEnabled(),
        fb->mSceneViewport.width>0 && fb->mSceneViewport.height>0 &&
        coverageState.active && !coverageState.rejected && SelacoMotionRuntime::Unambiguous() &&
            !SelacoMotionViews::Get().Rejected() && buffers->SceneReactive.Image &&
            buffers->SceneMotionDiagnostic.Image,
        candidateMetadata.reset});
    auto& finalizedMetadata=SelacoMotionMetadataStorage();
    finalizedMetadata.complete=coverage.complete;
    finalizedMetadata.reset=coverage.reset;
    finalizedMetadata.framegenComplete=false;
#endif
#if defined(__APPLE__) && TARGET_OS_IPHONE''')
edit(p,'        if(consumed){','        SelacoMotionCoverage::Get().Encoded(consumed);\n        if(consumed){')
p='src/common/rendering/vulkan/renderer/vk_renderstate.cpp'
edit(p,'\t// Is this the one we already have?','''    if(SelacoMotionDiagnostic() && mRenderTarget.Image==&fb->GetBuffers()->SceneColor &&
       pipelineKey.ColorMask && mRenderTarget.DrawBuffers!=5)
        SelacoMotionRuntime::Reject(); // A scene draw did not write full motion/reactive MRTs.
\t// Is this the one we already have?''')
# Hook actual engine discontinuity notification, not a guessed camera distance.
p='src/rendering/r_utility.cpp'
edit(p,'void R_ResetViewInterpolation ()\n{','void R_ResetViewInterpolation ()\n{\n    SelacoMotionCoverage::Invalidate();')
# This source includes r_utility.h; add runtime dependency explicitly.
edit(p,'#include "r_utility.h"','#include "r_utility.h"\n#include "hwrenderer/data/i_motion_coverage_runtime.h"')
for p,s in e.items():(r/p).write_text(s)
target=r/'src/common/rendering/hwrenderer/data'
overlay=Path(__file__).resolve().parents[1]/'overlays/gzselaco-ios'
(target/'i_motion_coverage_gate.h').write_text((overlay/'i_motion_coverage_gate.h').read_text(encoding='utf-8-sig'))
(target/'i_motion_coverage_runtime.h').write_text('''#pragma once
#include "i_motion_coverage_gate.h"
#include "hw_motion_diagnostic.h"
#include <atomic>
namespace SelacoMotionCoverage {
inline SelacoTemporal::CoverageGate& Get(){static SelacoTemporal::CoverageGate g;return g;}
inline std::atomic<std::uint64_t>& EpochStorage(){static std::atomic<std::uint64_t> e{1};return e;}
inline std::uint64_t Epoch(){return EpochStorage().load();}
inline void Invalidate(){EpochStorage().fetch_add(1);}
inline bool Option(const char* name){const char* p=std::getenv(name);return p&&p[0]=='1'&&p[1]==0;}
inline bool Enabled(){return SelacoMotionDiagnostic()&&Option("SELACO_TEMPORAL_SUPPORTED_FRAMES");}
inline bool JitterEnabled(){return Option("SELACO_TEMPORAL_JITTER");}
}
''')
print('Installed opt-in supported-frame gate after draw coverage; reset on skipped encode/recovery; framegen stays false')

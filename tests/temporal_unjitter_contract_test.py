#!/usr/bin/env python3
"""CPU contract check, not GPU image validation. Optional exact engine source root."""
import math,re,sys
from pathlib import Path

def source_sample(uv,origin,size,jitter):
    return max(origin+0.5,min(origin+size-0.5,origin+uv*size+jitter))

# A ramp translated +j has value (sample-j); source+ j recovers original ramp.
# Test positive/negative jitter, both dimensions, unequal native/source extents,
# and nonzero source viewport origin. Edge clamp cannot restore offscreen samples.
for origin,size in [(0,640),(37,333),(11,187)]:
    for jitter in [-0.49,-0.25,0,0.125,0.49]:
        for uv in [0.1,0.25,0.5,0.9]:
            sample=source_sample(uv,origin,size,jitter)
            assert math.isclose(sample-jitter,origin+uv*size,abs_tol=1e-10)
        assert origin+0.5<=source_sample(0,origin,size,jitter)<=origin+size-0.5
        assert origin+0.5<=source_sample(1,origin,size,jitter)<=origin+size-0.5

if len(sys.argv)>1:
    root=Path(sys.argv[1])
    reference=Path(sys.argv[2]) if len(sys.argv)>2 else root
    patcher=(reference/'src/common/rendering/hwrenderer/data/hw_shaderpatcher.cpp').read_text()
    effects=patcher.split('const FEffectShader effectshaders[] =',1)[1].split('};',1)[0]
    paths=re.findall(r'"(shaders/[^" ]+\.vp)"',effects)
    assert len(paths)==5 and set(paths)=={'shaders/glsl/main.vp'},paths
    shader=(root/'wadsrc/static/shaders/glsl/main.vp').read_text()
    main=shader.split('void main()',1)[1].split('#if !defined(SIMPLE)',1)[0]
    assert not re.search(r'\breturn\b',main), 'early exit requires jitter path audit'
    # main.vp jitter must sit with the common Vulkan coordinate conversion,
    # outside SIMPLE/material-specific conditionals. All five effects share it.
    if 'MotionJitter.xy' in shader:
        assert 'gl_Position.xy += MotionJitter.xy * gl_Position.w;' in main
    viewport=(root/'src/common/rendering/vulkan/renderer/vk_renderstate.cpp').read_text()
    assert 'viewport.height = (float)mViewportHeight;' in viewport
    fragment=root/'wadsrc/static/shaders/pp/motionfallback.fp'
    if fragment.exists():
        assert 'clamp(Offset+TexCoord*Scale,Minimum,Maximum)' in fragment.read_text()
        consumer=(root/'src/common/rendering/vulkan/renderer/vk_postprocess.cpp').read_text()
        for expression in [
            'u.Scale={src.width*iw,src.height*ih}',
            'u.Offset={(src.left+temporalMetadata.jitterX)*iw,(src.top+temporalMetadata.jitterY)*ih}',
            'u.Minimum={(src.left+0.5f)*iw,(src.top+0.5f)*ih}',
            'u.Maximum={(src.left+src.width-0.5f)*iw,(src.top+src.height-0.5f)*ih}',
            'fallback.SetInputSceneColor(0,PPFilterMode::Linear,PPWrapMode::Clamp)',
            'fallback.SetOutputCurrent()']:
            assert expression in consumer, expression
print('inverse-jitter sampling and common scene vertex-path contract PASS')

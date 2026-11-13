#!/usr/bin/env python3
"""Previous rigid/skeletal pose for unchanged model morph-frame pairs.
Apply after motion/sprites/views. Unsupported poses explicitly reject.
"""
from pathlib import Path
import sys
r=Path(sys.argv[1]);e={}
def edit(p,a,b):
 s=e.get(p,(r/p).read_text());assert s.count(a)==1,(p,a[:60],s.count(a));e[p]=s.replace(a,b)
base='src/common/rendering/'
edit(base+'hwrenderer/data/hw_viewpointuniforms.h','\tFVector4 mMotionSpriteCorners[4];','\tVSMatrix mMotionPreviousModel;\n\tFVector4 mMotionModelInfo = {0,0,0,0};\n\tFVector4 mMotionSpriteCorners[4];')
for rel,tabs in [('vulkan/shaders/vk_shader.cpp','\t\t'),('gl/gl_shader.cpp','\t\t\t')]:
 edit(base+rel,tabs+'vec4 MotionSpriteCorners[4];',tabs+'mat4 MotionPreviousModel;\n'+tabs+'vec4 MotionModelInfo;\n'+tabs+'vec4 MotionSpriteCorners[4];')
p='src/rendering/hwrenderer/hw_entrypoint.cpp'
edit(p,'#include "hwrenderer/data/i_motion_view_runtime.h"','#include "hwrenderer/data/i_motion_view_runtime.h"\n#include "hwrenderer/data/i_motion_model_runtime.h"')
edit(p,'            SelacoMotionRuntime::Begin(!motionHistory);','            SelacoMotionRuntime::Begin(!motionHistory);\n            SelacoMotionModels::Get().Begin(!motionHistory);')
edit(p,'            SelacoMotionRuntime::Commit();','            SelacoMotionRuntime::Commit();\n            SelacoMotionModels::Get().Commit();')
p='src/rendering/hwrenderer/hw_models.h'
edit(p,'\tint boneIndexBase = -1;','''\tint boneIndexBase = -1;
    const void* motionActor=nullptr;
    FModel* motionModel=nullptr;
    FGameTexture* motionSkin=nullptr;
    unsigned motionFrame1=0,motionFrame2=0;
    float motionInterpolation=0;
    TArray<VSMatrix> motionBones;
    bool motionWorld=false;
    void BeginMotionDraw(uint64_t draw, unsigned count);
    void EndMotionDraw();''')
edit(p,'\tModelRendererType GetType() const override','\tvoid SetMotionActor(const void* actor){motionActor=actor;}\n\tModelRendererType GetType() const override')
p='src/rendering/hwrenderer/scene/hw_sprites.cpp'
edit(p,'\t\t\tif(SelacoMotionDiagnostic())SelacoMotionRuntime::Reject(); // Bones/morph history unavailable.\n\t\t\tFHWModelRenderer renderer(di, state, dynlightindex);','\t\t\tFHWModelRenderer renderer(di, state, dynlightindex);\n            renderer.SetMotionActor(actor);')
p='src/rendering/hwrenderer/hw_models.cpp'
edit(p,'#include "hw_models.h"','#include "hw_models.h"\n#include "hwrenderer/data/i_motion_model_runtime.h"\n#include "hwrenderer/data/i_motion_sprite_runtime.h"\n#include "hwrenderer/data/hw_viewpointbuffer.h"')
a='void FHWModelRenderer::BeginDrawModel(FRenderStyle style, int smf_flags, const VSMatrix &objectToWorldMatrix, bool mirrored)\n{'
edit(p,a,a+'\n    motionWorld=true;')
a='void FHWModelRenderer::BeginDrawHUDModel(FRenderStyle style, const VSMatrix &objectToWorldMatrix, bool mirrored, int smf_flags)\n{'
edit(p,a,a+'\n    motionWorld=false;\n    if(SelacoMotionDiagnostic())SelacoMotionRuntime::Reject();')
edit(p,'\tstate.SetInterpolationFactor((float)inter);','\tstate.SetInterpolationFactor((float)inter);\n    motionInterpolation=float(inter);')
edit(p,'\tstate.SetMaterial(skin, UF_Skin,','\tmotionSkin=skin;\n\tstate.SetMaterial(skin, UF_Skin,')
edit(p,'\tauto mdbuff = static_cast<FModelVertexBuffer*>(model->GetVertexBuffer(GetType()));','\tif(SelacoMotionDiagnostic()){motionModel=model;motionFrame1=frame1;motionFrame2=frame2;motionBones=bones;}\n\tauto mdbuff = static_cast<FModelVertexBuffer*>(model->GetVertexBuffer(GetType()));')
edit(p,'\tstate.Draw(DT_Triangles, start, count);','\tBeginMotionDraw(uint64_t(uint32_t(start))<<1,unsigned(count));\n\tstate.Draw(DT_Triangles, start, count);\n    EndMotionDraw();')
edit(p,'\tstate.DrawIndexed(DT_Triangles, int(offset / sizeof(unsigned int)), numIndices);','\tBeginMotionDraw((uint64_t(offset)<<1)|1,unsigned(numIndices));\n\tstate.DrawIndexed(DT_Triangles, int(offset / sizeof(unsigned int)), numIndices);\n    EndMotionDraw();')
e[p]+='''
void FHWModelRenderer::BeginMotionDraw(uint64_t draw,unsigned count)
{
    if(!SelacoMotionDiagnostic())return;
    auto vp=di->VPUniforms;
    bool valid=motionWorld && motionActor && motionModel && !di->mCurrentPortal;
    SelacoMotionModels::History::Pose now,old;
    now.model=state.mModelMatrix;now.frame1=motionFrame1;now.frame2=motionFrame2;
    now.count=count;now.appearance=reinterpret_cast<uintptr_t>(motionSkin);now.interpolation=motionInterpolation;
    for(unsigned i=0;i<motionBones.Size();++i)now.bones.push_back(motionBones[i]);
    if(boneIndexBase>=0 && now.bones.empty())valid=false;
    const auto generation=motionActor?SelacoMotionRuntime::Generation(motionActor):0;
    valid=valid && generation && SelacoMotionModels::Get().Capture(
        {reinterpret_cast<uintptr_t>(motionActor),generation,reinterpret_cast<uintptr_t>(motionModel),draw},now,old);
    int previousBase=-1;
    if(valid && !old.bones.empty()) {
        TArray<VSMatrix> previousBones;
        for(const auto& b:old.bones)previousBones.Push(b);
        screen->mBones->Map();previousBase=screen->mBones->UploadBones(previousBones);screen->mBones->Unmap();
        if(previousBase<0)valid=false;
    }
    vp.mMotionPreviousModel=valid?old.model:now.model;
    vp.mMotionModelInfo={1.f,valid?1.f:0.f,float(previousBase),valid?old.interpolation:0.f};
    if(!valid)SelacoMotionRuntime::Reject();
    screen->mViewpoints->SetViewpoint(state,&vp);
}
void FHWModelRenderer::EndMotionDraw()
{
    if(SelacoMotionDiagnostic())screen->mViewpoints->Bind(state,di->vpIndex);
}
'''
p='wadsrc/static/shaders/glsl/main.vp'
edit(p,'BonesResult ApplyBones();','''BonesResult ApplyBones();
#ifdef VULKAN_COORDINATE_SYSTEM
vec4 MotionPreviousPosition();
#endif''')
edit(p,'    if(MotionSpriteInfo.x > 0.5) {','''    if(MotionModelInfo.x > 0.5) {
        if(MotionModelInfo.y > 0.5)
            vMotionPreviousClip=PreviousProjectionMatrix * PreviousViewMatrix * MotionPreviousModel * MotionPreviousPosition();
        else vMotionPreviousClip=vec4(0.0,0.0,0.0,-1.0);
    }
    if(MotionSpriteInfo.x > 0.5) {''')
e[p]+='''
#ifdef VULKAN_COORDINATE_SYSTEM
vec4 MotionPreviousPosition()
{
    vec4 previous=aPosition;
#ifndef SIMPLE
    if(MotionModelInfo.z>=0.0 && aBoneWeight!=vec4(0.0)) {
        previous=vec4(0.0);
        float sum=aBoneWeight.x+aBoneWeight.y+aBoneWeight.z+aBoneWeight.w;
        vec4 weights=aBoneWeight/sum;
        for(int i=0;i<4;++i)if(weights[i]!=0.0)
            previous+=(bones[int(MotionModelInfo.z)+int(aBoneSelector[i])]*aPosition)*weights[i];
        previous.w=1.0;
    }
    previous=mix(previous,aVertex2,MotionModelInfo.w);
#endif
    return previous;
}
#endif
'''
for p,s in e.items():(r/p).write_text(s)
target=r/'src/common/rendering/hwrenderer/data'
overlay=Path(__file__).resolve().parents[1]/'overlays/gzselaco-ios'
(target/'i_motion_model_history.h').write_text((overlay/'i_motion_model_history.h').read_text(encoding='utf-8-sig'))
(target/'i_motion_model_runtime.h').write_text('''#pragma once
#include "i_motion_model_history.h"
#include "matrix.h"
namespace SelacoMotionModels {using History=SelacoTemporal::ModelHistory<VSMatrix>;inline History& Get(){static auto* s=new History;return *s;}}
''')
print('Applied previous model transform/bone pose; changed frame pairs reject; complete=false')

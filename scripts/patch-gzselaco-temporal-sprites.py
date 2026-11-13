#!/usr/bin/env python3
"""Apply after temporal-motion; main-view billboard prior-geometry diagnostic."""
from pathlib import Path
import sys
root=Path(sys.argv[1]);edits={}
def edit(rel,old,new):
 s=edits.get(rel,(root/rel).read_text());assert s.count(old)==1,(rel,old[:65],s.count(old));edits[rel]=s.replace(old,new)
base='src/common/rendering/'
edit(base+'hwrenderer/data/hw_viewpointuniforms.h','\tVSMatrix mPreviousProjectionMatrix;','\tFVector4 mMotionSpriteCorners[4];\n\tFVector4 mMotionSpriteInfo = {0,0,0,0};\n\tVSMatrix mPreviousProjectionMatrix;')
for rel,tabs in [('vulkan/shaders/vk_shader.cpp','\t\t'),('gl/gl_shader.cpp','\t\t\t')]:
 edit(base+rel,tabs+'mat4 PreviousProjectionMatrix;',tabs+'vec4 MotionSpriteCorners[4];\n'+tabs+'vec4 MotionSpriteInfo;\n'+tabs+'mat4 PreviousProjectionMatrix;')
p='src/rendering/hwrenderer/hw_entrypoint.cpp'
edit(p,'#include <chrono>','#include <chrono>\n#include "hwrenderer/data/i_motion_sprite_runtime.h"')
edit(p,'            SelacoMotionMetadataStorage() = {0.f,0.f,!motionHistory,false};','            SelacoMotionRuntime::Begin(!motionHistory);\n            SelacoMotionMetadataStorage() = {0.f,0.f,!motionHistory,false};')
edit(p,'            motionCamera = camera; motionTime = motionNow;','            motionCamera = camera; motionTime = motionNow;\n            SelacoMotionRuntime::Commit();')
p='src/common/objects/dobject.cpp'
edit(p,'#include "dobject.h"','#include "dobject.h"\n#include "hwrenderer/data/i_motion_sprite_runtime.h"\n#include "hwrenderer/data/hw_motion_diagnostic.h"')
edit(p,'DObject::~DObject ()\n{','DObject::~DObject ()\n{\n    if(SelacoMotionDiagnostic())SelacoMotionRuntime::Forget(this);')
p='src/rendering/hwrenderer/scene/hw_drawstructs.h'
edit(p,'class HWSprite\n{\npublic:','class HWSprite\n{\npublic:\n    float motionPreviousCorners[4][3] = {};\n    bool motionPreviousValid = false;')
p='src/rendering/hwrenderer/scene/hw_sprites.cpp'
edit(p,'#include "p_local.h"','#include "p_local.h"\n#include "hwrenderer/data/i_motion_sprite_runtime.h"\n#include "hwrenderer/data/hw_viewpointbuffer.h"')
edit(p,'\t\tpolyoffset = CalculateVertices(di, v, &di->Viewpoint.Pos);','''\t\tpolyoffset = CalculateVertices(di, v, &di->Viewpoint.Pos);
        motionPreviousValid = false;
        if(SelacoMotionDiagnostic()) {
            if(actor && !isparticle && !di->mCurrentPortal) {
                float corners[4][3];for(int n=0;n<4;++n)for(int c=0;c<3;++c)corners[n][c]=v[n][c];
                const float uv[4]={ul,ur,vt,vb};
                auto previous=SelacoMotionRuntime::Capture(actor,texture,uv,corners);
                motionPreviousValid=previous.valid();
                if(motionPreviousValid)for(int n=0;n<4;++n){
                    motionPreviousCorners[n][0]=previous.previousWorldVertices[n].x;
                    motionPreviousCorners[n][1]=previous.previousWorldVertices[n].y;
                    motionPreviousCorners[n][2]=previous.previousWorldVertices[n].z;
                }
            } else SelacoMotionRuntime::Reject();
        }''')
s=edits[p];draw='state.Draw(DT_TriangleStrip, vertexindex, 4);';assert s.count(draw)==2
replacement='''{
                    if(SelacoMotionDiagnostic()) {
                        auto motionVP=di->VPUniforms;
                        const bool valid=motionPreviousValid && SelacoMotionRuntime::Unambiguous() && !di->mCurrentPortal;
                        motionVP.mMotionSpriteInfo={1.f,float(vertexindex),valid?1.f:0.f,0.f};
                        for(int n=0;n<4;++n)motionVP.mMotionSpriteCorners[n]={motionPreviousCorners[n][0],motionPreviousCorners[n][1],motionPreviousCorners[n][2],1.f};
                        screen->mViewpoints->SetViewpoint(state,&motionVP);
                    }
                    state.Draw(DT_TriangleStrip, vertexindex, 4);
                    if(SelacoMotionDiagnostic())screen->mViewpoints->Bind(state,di->vpIndex);
                }'''
edits[p]=s.replace(draw,replacement)
edit(p,'\t\t\tFHWModelRenderer renderer(di, state, dynlightindex);','\t\t\tif(SelacoMotionDiagnostic())SelacoMotionRuntime::Reject(); // Bones/morph history unavailable.\n\t\t\tFHWModelRenderer renderer(di, state, dynlightindex);')
p='src/rendering/hwrenderer/scene/hw_drawinfo.cpp'
edit(p,'#include "hw_drawinfo.h"','#include "hw_drawinfo.h"\n#include "hwrenderer/data/i_motion_sprite_runtime.h"')
edit(p,'\tnew_di->mCurrentPortal = gp;','\tnew_di->mCurrentPortal = gp;\n    if(SelacoMotionDiagnostic())SelacoMotionRuntime::Reject(); // Portal history unavailable.')
p='wadsrc/static/shaders/glsl/main.vp'
edit(p,'    vMotionPreviousClip = PreviousProjectionMatrix * PreviousViewMatrix * worldcoord;','''    vMotionPreviousClip = PreviousProjectionMatrix * PreviousViewMatrix * worldcoord;
    if(MotionSpriteInfo.x > 0.5) {
        int corner = gl_VertexIndex - int(MotionSpriteInfo.y);
        if(MotionSpriteInfo.z > 0.5 && corner >= 0 && corner < 4)
            vMotionPreviousClip = PreviousProjectionMatrix * PreviousViewMatrix * MotionSpriteCorners[corner];
        else vMotionPreviousClip = vec4(0.0,0.0,0.0,-1.0);
    }''')
for rel,s in edits.items():(root/rel).write_text(s)
for name in ['i_motion_sprite_runtime.h','i_temporal_primitive_history.h','RTGL-MIT-LICENSE.txt']:
 source=Path(__file__).resolve().parents[1]/'overlays/gzselaco-ios'/name
 (root/(base+'hwrenderer/data/'+name)).write_text(source.read_text(encoding='utf-8-sig'))
print('Applied real main-view billboard previous-corner path; models/portals reject; completeMotion=false')

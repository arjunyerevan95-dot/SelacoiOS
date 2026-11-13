#!/usr/bin/env python3
"""Observed dynamic-world rejection hooks; NOT world motion reconstruction."""
from pathlib import Path
import sys
r=Path(sys.argv[1]);e={}
def edit(p,a,b):
 s=e.get(p,(r/p).read_text());assert s.count(a)==1,(p,a[:60],s.count(a));e[p]=s.replace(a,b)
p='src/rendering/hwrenderer/hw_vertexbuilder.cpp'
edit(p,'#include "hw_vertexbuilder.h"','#include "hw_vertexbuilder.h"\n#include "hwrenderer/data/i_motion_sprite_runtime.h"\n#include "hwrenderer/data/hw_motion_diagnostic.h"')
edit(p,'static void UpdatePlaneVertices(FFlatVertexBuffer *fvb, sector_t* sec, int plane)\n{','''static void UpdatePlaneVertices(FFlatVertexBuffer *fvb, sector_t* sec, int plane)
{
    // Changes persistent vertex positions in place; prior world stream absent.
    if(SelacoMotionDiagnostic())SelacoMotionRuntime::Reject();''')
p='src/rendering/hwrenderer/scene/hw_bsp.cpp'
edit(p,'#include "hwrenderer/scene/hw_drawinfo.h"','#include "hwrenderer/scene/hw_drawinfo.h"\n#include "hwrenderer/data/i_motion_sprite_runtime.h"')
edit(p,'void HWDrawInfo::AddPolyobjs(subsector_t *sub)\n{','''void HWDrawInfo::AddPolyobjs(subsector_t *sub)
{
    // Polyobject BSP vertices are rebuilt; previous instance geometry absent.
    if(SelacoMotionDiagnostic())SelacoMotionRuntime::Reject();''')
p='src/rendering/hwrenderer/scene/hw_flats.cpp'
edit(p,'#include "hw_drawstructs.h"','#include "hw_drawstructs.h"\n#include "hwrenderer/data/i_motion_sprite_runtime.h"')
edit(p,'void HWFlat::DrawFlat(HWDrawInfo *di, FRenderState &state, bool translucent)\n{','''void HWFlat::DrawFlat(HWDrawInfo *di, FRenderState &state, bool translucent)
{
    // These paths do not provide matching opaque depth/motion or stable topology.
    if(SelacoMotionDiagnostic() && (translucent || hacktype || plane.plane.dithertransflag))
        SelacoMotionRuntime::Reject();''')
for p,s in e.items():(r/p).write_text(s)
print('Applied observed dynamic plane/polyobject/flat coverage rejection hooks')

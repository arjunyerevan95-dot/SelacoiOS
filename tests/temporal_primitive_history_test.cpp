#include "i_temporal_primitive_history.h"
#include <cassert>
#include <limits>
using namespace SelacoTemporal;
int main() {
 PrimitiveGeometryCache c; PrimitiveKey k{1,1,1,1};
 PrimitiveGeometry g{{{0,0,0},{1,0,0},{0,1,0}},{0,1,2},1,1};
 assert(c.Capture(k,g).reason==PrimitiveReject::NoFrame);
 assert(c.Begin(1)); assert(!c.Begin(1)); assert(!c.Capture(k,g).valid()); assert(c.Commit());
 assert(c.Begin(2)); g.vertices[0].x=2;
 auto h=c.Capture(k,g); assert(h.valid()&&h.previousWorldVertices[0].x==0); assert(c.Commit());
 assert(h.previousWorldVertices[0].x==0); // Owning lifetime across commit.
 assert(c.Begin(3)); auto generation=k;generation.generation++;
 assert(!c.Capture(generation,g).valid()); auto view=k;view.view++;
 assert(!c.Capture(view,g).valid()); auto prim=k;prim.primitive++;
 assert(!c.Capture(prim,g).valid()); c.Abort();
 assert(c.Begin(3)); auto topology=g;topology.indices={0,2,1};
 assert(c.Capture(k,topology).reason==PrimitiveReject::Topology);c.Abort();
 assert(c.Begin(3)); topology=g;topology.topologyRevision++;
 assert(c.Capture(k,topology).reason==PrimitiveReject::Topology);c.Abort();
 assert(c.Begin(3)); auto appearance=g;appearance.appearanceRevision++;
 assert(c.Capture(k,appearance).reason==PrimitiveReject::Appearance);c.Abort();
 assert(c.Begin(3)); assert(c.Capture(k,g).valid());
 assert(c.Capture(k,g).reason==PrimitiveReject::Duplicate);assert(!c.FrameUnambiguous());c.Commit();
 assert(c.Begin(4)); assert(!c.Capture(k,g).valid());c.Commit();
 assert(c.Begin(6)); assert(!c.Capture(k,g).valid());c.Commit(); // Skipped frame reset.
 assert(c.Begin(7)); c.Commit(); // Missing primitive is evicted.
 assert(c.Begin(8)); assert(!c.Capture(k,g).valid());c.Abort();
 c.Reset();assert(c.Begin(1));auto bad=g;bad.indices[0]=100;
 assert(c.Capture(k,bad).reason==PrimitiveReject::Invalid);
 bad=g;bad.vertices[0].x=std::numeric_limits<float>::quiet_NaN();
 assert(c.Capture(k,bad).reason==PrimitiveReject::Invalid);c.Abort();
 PrimitiveGeometryCache small(4,1);small.Begin(1);
 assert(small.Capture(k,g).reason==PrimitiveReject::Budget);
}

#include "i_temporal_history.h"
#include <cassert>
#include <limits>
using namespace SelacoTemporal;
int main() {
    History history;
    Frame frame{{640,360},{1280,720},1,0.,false,true};
    auto d = history.Begin(frame);
    assert(d.temporalAllowed && !d.interpolateAllowed && d.reason == Reset::FirstFrame);
    history.Commit(frame,d); frame.timeSeconds += 1./60.;
    d=history.Begin(frame); assert(d.interpolateAllowed && d.reason == Reset::None);
    history.Commit(frame,d); frame.cameraCut=true;
    d=history.Begin(frame); assert(d.reason==Reset::CameraCut && !d.interpolateAllowed);
    frame.cameraCut=false; frame.viewKey=2;
    assert(history.Begin(frame).reason==Reset::ViewChanged);
    frame.viewKey=1; frame.input.width=320;
    assert(history.Begin(frame).reason==Reset::Resize);
    frame.input.width=640; frame.completeMotion=false;
    assert(!history.Begin(frame).temporalAllowed);
    frame.completeMotion=true; frame.timeSeconds=1.;
    assert(history.Begin(frame).reason==Reset::TimeDiscontinuity);
    history.Invalidate(); assert(history.Begin(frame).reason==Reset::Explicit);
    frame.timeSeconds=std::numeric_limits<double>::quiet_NaN();
    assert(!history.Begin(frame).temporalAllowed);
    for (unsigned i=0;i<100;++i) { auto j=SampleJitter(i); assert(j.x>=-.5f && j.x<=.5f && j.y>=-.5f && j.y<=.5f); }
}

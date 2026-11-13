#include "i_motion_coverage_gate.h"
#include <cassert>
using namespace SelacoTemporal;
int main(){
 CoverageGate g;CoverageEvidence e{1,1,640,360,1280,720,true,true,true,false};
 auto d=g.Finalize(e);assert(d.complete&&d.reset);g.Encoded(true);
 e.serial++;d=g.Finalize(e);assert(d.complete&&!d.reset);g.Encoded(false);
 e.serial++;d=g.Finalize(e);assert(d.complete&&d.reset);g.Encoded(true);
 e.serial++;e.drawsComplete=false;d=g.Finalize(e);assert(!d.complete);g.Encoded(false);
 e.serial++;e.drawsComplete=true;d=g.Finalize(e);assert(d.complete&&d.reset);g.Encoded(true);
 e.serial++;e.epoch++;d=g.Finalize(e);assert(d.complete&&d.reset);g.Encoded(true);
 e.serial++;e.width++;d=g.Finalize(e);assert(d.complete&&d.reset);g.Encoded(true);
 d=g.Finalize(e);assert(!d.complete);
 e.serial++;e.jitterReady=false;assert(!g.Finalize(e).complete);
 e.jitterReady=true;e.requested=false;assert(!g.Finalize(e).complete);
 e.requested=true;e.width=0;assert(!g.Finalize(e).complete);
}

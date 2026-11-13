#include "../overlays/gzselaco-ios/i_temporal_present_pacer.h"
#include <cassert>
int main() {
    IOSTemporalPresentPacer p; IOSTemporalPresentPacer::Pair a,b;
    assert(!p.Reserve(1000000000,16666667,33333334,true,true,a));
    assert(!p.Reserve(1000000000,8333333,16666666,false,true,a));
    assert(!p.Reserve(1000000000,8333333,16666666,true,false,a));
    assert(!p.Reserve(1000000000,8333333,33333333,true,true,a));
    assert(p.Reserve(1000000000,8333333,16666666,true,true,a));
    assert(a.generatedNS<a.realNS && a.generatedID<a.realID);
    assert(!p.Reserve(1000000001,8333333,16666666,true,true,b));
    assert(!p.Retire(a.generatedID,a.generatedNS));
    assert(p.Retire(a.realID,a.realNS));
    assert(p.Reserve(a.realNS,8333333,16666666,true,true,b));
    assert(b.generatedID>a.realID && b.generatedNS>a.realNS);
    p.ResetAfterDrain();
    assert(!p.HasPending());
    assert(!p.Reserve(UINT64_MAX-1,8333333,16666666,true,true,b));
}

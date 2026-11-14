#pragma once
#include <cstdint>
#include <limits>

// Bounded generated->real presentation planning. Times must use the Vulkan
// display-timing monotonic clock. This does not sleep or manufacture more FPS.
class IOSTemporalPresentPacer
{
public:
    struct Pair { uint64_t generatedNS=0, realNS=0; uint32_t generatedID=0, realID=0; };
    static bool CadenceSupported(uint64_t refresh,uint64_t delta) {
        return refresh>=4000000 && refresh<=16666668 && delta>=refresh*3/2 && delta<=40000000;
    }
    bool Reserve(uint64_t now, uint64_t refresh, uint64_t realDelta,
                 bool completeHistory, bool fifoTimingSupported, Pair &out)
    {
        out={};
        // 30->60 permitted; this does not increase input/simulation cadence.
        if (pending.realID || !completeHistory || !fifoTimingSupported ||
            !CadenceSupported(refresh,realDelta) ||
            nextID>std::numeric_limits<uint32_t>::max()-2) return false;
        const uint64_t ticks=(realDelta+refresh)/(2*refresh);
        const uint64_t step=(ticks?ticks:1)*refresh;
        if(now>std::numeric_limits<uint64_t>::max()-step*3)return false;
        uint64_t generated=now+step;
        if (lastReal>now && lastReal<generated) generated=lastReal+step;
        if (generated>now+step*2) return false;
        out={generated,generated+step,nextID,nextID+1};
        nextID+=2; pending=out; submitted=false; return true;
    }
    bool MarkSubmitted(const Pair& pair) {
        if(!pending.realID || pair.realID!=pending.realID || pair.generatedID!=pending.generatedID)return false;
        submitted=true;return true;
    }
    // Only before any swapchain acquisition/submission for this reservation.
    bool CancelUnsubmitted(const Pair& pair) {
        if(submitted || !pending.realID || pair.realID!=pending.realID || pair.generatedID!=pending.generatedID)return false;
        pending={};return true;
    }
    // Call only after actual display-timing feedback reports the real ID.
    // GPU command completion alone is not evidence that a drawable was shown.
    bool Retire(uint32_t realID, uint64_t actualTime)
    {
        if (!submitted || !pending.realID || realID!=pending.realID) return false;
        lastReal=actualTime; pending={};submitted=false; return true;
    }
    // Abort requires caller to retire/cancel submitted presentation resources.
    // Never use this merely to free the capacity for another in-flight pair.
    void ResetAfterDrain() { pending={}; lastReal=0;submitted=false; }
    bool HasPending() const { return pending.realID!=0; }
private:
    Pair pending{};
    bool submitted=false;
    uint64_t lastReal=0;
    uint32_t nextID=1;
};


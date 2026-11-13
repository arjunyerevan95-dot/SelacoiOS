#pragma once
#include <cstdint>
#include <limits>

// Bounded generated->real presentation planning. Times must use the Vulkan
// display-timing monotonic clock. This does not sleep or manufacture more FPS.
class IOSTemporalPresentPacer
{
public:
    struct Pair { uint64_t generatedNS=0, realNS=0; uint32_t generatedID=0, realID=0; };
    bool Reserve(uint64_t now, uint64_t refresh, uint64_t realDelta,
                 bool completeHistory, bool fifoTimingSupported, Pair &out)
    {
        out={};
        // One outstanding pair, 90+ Hz display and 45+ real FPS only. A 30 FPS
        // producer is not promoted to a low-latency 60 FPS claim.
        if (pending.realID || !completeHistory || !fifoTimingSupported || refresh<4000000 ||
            refresh>11111112 || realDelta<refresh*3/2 || realDelta>refresh*5/2 ||
            nextID>std::numeric_limits<uint32_t>::max()-2 ||
            now>std::numeric_limits<uint64_t>::max()-refresh*3) return false;
        // Never queue a stale generated frame or more than two ticks ahead.
        uint64_t generated=now+refresh;
        if (lastReal>now && lastReal<generated) generated=lastReal+refresh;
        if (generated>now+refresh*2) return false;
        out={generated,generated+refresh,nextID,nextID+1};
        nextID+=2; pending=out; return true;
    }
    // Call only after actual display-timing feedback reports the real ID.
    // GPU command completion alone is not evidence that a drawable was shown.
    bool Retire(uint32_t realID, uint64_t actualTime)
    {
        if (!pending.realID || realID!=pending.realID) return false;
        lastReal=actualTime; pending={}; return true;
    }
    // Abort requires caller to retire/cancel submitted presentation resources.
    // Never use this merely to free the capacity for another in-flight pair.
    void ResetAfterDrain() { pending={}; lastReal=0; }
    bool HasPending() const { return pending.realID!=0; }
private:
    Pair pending{};
    uint64_t lastReal=0;
    uint32_t nextID=1;
};


#pragma once
#include <cstdint>
// Renderer-thread-only creation throttle; never sleeps, changes render history,
// or bypasses resource retirement. Frame reset/jitter is NOT a config change.
struct IOSMetalFXCreateKey {
    std::uintptr_t owner=0,device=0;
    std::uint32_t width=0,height=0,outputWidth=0,outputHeight=0;
    bool interpolation=false;
    bool operator==(const IOSMetalFXCreateKey& b) const {
        return owner==b.owner && device==b.device && width==b.width && height==b.height &&
            outputWidth==b.outputWidth && outputHeight==b.outputHeight && interpolation==b.interpolation;
    }
};
class IOSMetalFXCreateRetry {
    IOSMetalFXCreateKey key_{};
    bool known_=false;
    unsigned failures_=0;
    std::uint64_t failedAt_=0;
public:
    bool Allow(const IOSMetalFXCreateKey& key,std::uint64_t now) {
        if(!known_ || !(key==key_)) {key_=key;known_=true;failures_=0;}
        if(!failures_)return true;
        // Clamp at four seconds and compare elapsed time without addition overflow.
        const std::uint64_t delay=500000000ULL << (failures_>4?3:failures_-1);
        return now<failedAt_ || now-failedAt_>=delay;
    }
    void Failed(std::uint64_t now) {failedAt_=now;if(failures_<4)++failures_;}
    void Succeeded() {failures_=0;}
};

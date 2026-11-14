#pragma once
#include <atomic>
#include <cstdint>
#include <cstdlib>
#include <cstring>
// Shared inline state: render thread owns GPU work; UI only publishes requests.
namespace SelacoCompare {
inline std::atomic<int> overrideEnabled{-1};
inline std::atomic<uint64_t> rendered{0}, encoded{0};
inline bool Enabled(){int v=overrideEnabled.load(std::memory_order_relaxed);if(v>=0)return v!=0;const char* e=std::getenv("SELACO_IOS_METALFX_FRAMEGEN");return e && !std::strcmp(e,"1");}
inline void SetEnabled(bool value){overrideEnabled.store(value?1:0,std::memory_order_relaxed);}
// Encoded is NOT GPU completion or proof that a generated frame was displayed.
inline void Render(){rendered.fetch_add(1,std::memory_order_relaxed);}
inline void Encode(){encoded.fetch_add(1,std::memory_order_relaxed);}
}

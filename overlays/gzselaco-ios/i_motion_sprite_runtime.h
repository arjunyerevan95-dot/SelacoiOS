#pragma once
#include "i_temporal_primitive_history.h"
#include <mutex>
#include <cstring>
namespace SelacoMotionRuntime {
struct Runtime { SelacoTemporal::PrimitiveGeometryCache cache; std::map<const void*,std::uint64_t> generations; std::mutex mutex; std::uint64_t next=1,serial=0; bool active=false,rejected=false,reset=true; };
inline Runtime& Get(){static auto* s=new Runtime;return *s;}
inline void Forget(const void* o){auto& s=Get();std::lock_guard<std::mutex> l(s.mutex);s.generations.erase(o);}
inline std::uint64_t Generation(const void* o){auto& s=Get();std::lock_guard<std::mutex> l(s.mutex);auto i=s.generations.find(o);if(i!=s.generations.end())return i->second;if(s.next==UINT64_MAX)return 0;return s.generations.emplace(o,s.next++).first->second;}
inline void Begin(bool reset){auto& s=Get();if(reset)s.cache.Reset();if(s.active)s.cache.Abort();s.active=s.cache.Begin(++s.serial);s.rejected=false;s.reset=reset;}
inline void Commit(){auto& s=Get();if(s.active)s.cache.Commit();s.active=false;}
inline void Reject(){Get().rejected=true;}
struct Metadata {
 float jitterPixelsX=0, jitterPixelsY=0;
 bool reset=true, completeMotion=false, rejected=true;
 std::uint64_t frameSerial=0;
};
inline Metadata GetMetadata() {
 const auto& s=Get();
 // Projection jitter and all-object coverage are NOT implemented.
 return {0.f,0.f,s.reset,false,s.rejected,s.serial};
}
inline bool Unambiguous(){return Get().active&&Get().cache.FrameUnambiguous();}
inline std::uint64_t Appearance(const void* t,const float* uv){std::uint64_t h=reinterpret_cast<std::uintptr_t>(t);for(int i=0;i<4;++i){std::uint32_t b;std::memcpy(&b,uv+i,sizeof(b));h=(h^b)*1099511628211ull;}return h;}
inline SelacoTemporal::PrimitiveHistory Capture(const void* actor,const void* texture,const float* uv,const float corners[4][3]){
 auto& s=Get();SelacoTemporal::PrimitiveHistory missing;if(!s.active||!actor)return missing;
 auto generation=Generation(actor);if(!generation){s.rejected=true;return missing;}
 SelacoTemporal::PrimitiveGeometry g;for(int i=0;i<4;++i)g.vertices.push_back({corners[i][0],corners[i][1],corners[i][2]});
 g.indices={0,1,2,2,1,3};g.topologyRevision=1;g.appearanceRevision=Appearance(texture,uv);
 auto r=s.cache.Capture({reinterpret_cast<std::uintptr_t>(actor),generation,1,0},g);if(!r.valid())s.rejected=true;return r;
}
}

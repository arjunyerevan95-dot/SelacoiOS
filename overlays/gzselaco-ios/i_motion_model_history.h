#pragma once
#include <map>
#include <vector>
#include <tuple>
#include <cstdint>
namespace SelacoTemporal {
template<class Matrix> class ModelHistory {
public:
 struct Key {
  std::uint64_t object,generation,model,draw;
  bool operator<(const Key& b)const{return std::tie(object,generation,model,draw)<std::tie(b.object,b.generation,b.model,b.draw);}
 };
 struct Pose {
  Matrix model;
  std::vector<Matrix> bones;
  unsigned frame1=0,frame2=0,count=0;
  std::uint64_t appearance=0;
  float interpolation=0;
 };
private:
 std::map<Key,Pose> previous_,pending_;
 bool active_=false;std::size_t boneMatrices_=0;
public:
 void Begin(bool reset){if(reset)previous_.clear();pending_.clear();active_=true;boneMatrices_=0;}
 bool Capture(Key key,const Pose& now,Pose& old){
  if(!active_||pending_.size()>=16384||now.bones.size()>4096||now.bones.size()>65536-boneMatrices_)return false;
  if(!pending_.emplace(key,now).second)return false;
  boneMatrices_+=now.bones.size();
  auto p=previous_.find(key);if(p==previous_.end())return false;
  const auto& v=p->second;
  // Current vertex attributes can represent the old pose only for the same
  // morph-frame pair. Frame transitions deliberately reject for one frame.
  if(v.frame1!=now.frame1||v.frame2!=now.frame2||v.count!=now.count||v.appearance!=now.appearance||v.bones.size()!=now.bones.size())return false;
  old=v;return true;
 }
 void Commit(){if(active_)previous_=std::move(pending_);pending_.clear();active_=false;}
};
}

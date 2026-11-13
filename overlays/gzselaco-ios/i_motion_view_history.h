#pragma once
#include <map>
#include <vector>
#include <cstdint>
namespace SelacoTemporal {
// Ordered full recursion paths, not a hash that can alias distinct portals.
template<class Matrix> class ViewHistory {
public:
 using Key=std::vector<std::uintptr_t>;
 struct Pair {Matrix projection,view;};
private:
 std::map<Key,Pair> previous_,pending_;
 bool active_=false, rejected_=false;
public:
 void Begin(bool reset){if(reset)previous_.clear();pending_.clear();active_=true;rejected_=false;}
 bool Capture(const Key& key,const Pair& current,Pair& previous){
  if(!active_){rejected_=true;return false;}
  if(!pending_.emplace(key,current).second){rejected_=true;return false;}
  auto p=previous_.find(key);if(p==previous_.end()){rejected_=true;return false;}
  previous=p->second;return true;
 }
 void Commit(){if(active_)previous_=std::move(pending_);pending_.clear();active_=false;}
 bool Rejected()const{return rejected_;}
};
}

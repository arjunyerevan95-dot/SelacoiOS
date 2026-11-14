#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
namespace SelacoIOS {
// Editor-only ownership. After a pinch lifts, consume its remaining contact until
// both are gone: never reinterpret a pinch tail as a drag or gameplay gesture.
struct EditorGesture {
 enum class Change { None, Drag, Resize };
 uintptr_t first=0,second=0; int control=-1;
 double ax=0,ay=0,bx=0,by=0,startDistance=0,startSize=44,size=44;
 bool draining=false;
 void reset(){*this=EditorGesture{};}
 bool begin(uintptr_t id,double x,double y,int hit,double currentSize){
  if(!id||draining||!std::isfinite(x)||!std::isfinite(y))return false;
  if(!first){if(hit<0)return false;first=id;control=hit;ax=x;ay=y;size=std::isfinite(currentSize)?std::clamp(currentSize,44.,140.):44.;return true;}
  if(id==first||id==second||second)return false;
  second=id;bx=x;by=y;startDistance=std::max(8.,std::hypot(bx-ax,by-ay));startSize=size;return true;
 }
 Change move(uintptr_t id,double x,double y){
  if(draining||!std::isfinite(x)||!std::isfinite(y))return Change::None;
  if(id==first){ax=x;ay=y;}else if(id==second&&second){bx=x;by=y;}else return Change::None;
  if(second){size=std::clamp(startSize*std::hypot(bx-ax,by-ay)/startDistance,44.,140.);return Change::Resize;}
  return Change::Drag;
 }
 void end(uintptr_t id){
  if(id!=first&&id!=second)return;
  const bool pair=second!=0||draining;
  if(id==first)first=0;
  if(id==second)second=0;
  if(!first&&!second){reset();return;}if(pair)draining=true;
 }
};
}

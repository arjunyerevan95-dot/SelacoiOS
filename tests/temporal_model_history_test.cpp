#include "i_motion_model_history.h"
#include <array>
#include <cassert>
int main(){
 using H=SelacoTemporal::ModelHistory<std::array<float,4>>;
 H h;H::Key key{1,1,1,0};H::Pose p,old;
 p.model={1,0,0,0};p.bones={{{1,2,3,4}}};p.frame1=0;p.frame2=1;p.count=3;p.appearance=4;
 h.Begin(true);assert(!h.Capture(key,p,old));h.Commit();
 h.Begin(false);p.model[0]=2;p.bones[0][0]=5;p.interpolation=.5;
 assert(h.Capture(key,p,old));assert(old.model[0]==1&&old.bones[0][0]==1&&old.interpolation==0);h.Commit();
 h.Begin(false);p.frame2=2;assert(!h.Capture(key,p,old));h.Commit();
 h.Begin(false);assert(h.Capture(key,p,old));assert(!h.Capture(key,p,old));h.Commit();
 h.Begin(false);key.generation++;assert(!h.Capture(key,p,old));h.Commit();
 h.Begin(false);p.appearance++;assert(!h.Capture(key,p,old));h.Commit();
 h.Begin(true);assert(!h.Capture(key,p,old));h.Commit();
 h.Begin(false);p.bones.resize(4097);assert(!h.Capture(key,p,old));h.Commit();
}

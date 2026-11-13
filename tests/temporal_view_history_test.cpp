#include "i_motion_view_history.h"
#include <cassert>
#include <array>
int main(){
 using H=SelacoTemporal::ViewHistory<std::array<float,2>>;
 H h;H::Pair now{{1,2},{3,4}},p{};
 h.Begin(true);assert(!h.Capture({1},now,p));h.Commit();
 h.Begin(false);now.view={5,6};assert(h.Capture({1},now,p));assert(p.view[0]==3);
 assert(!h.Capture({1,2},now,p));assert(!h.Capture({1},now,p));h.Commit();
 h.Begin(false);assert(h.Capture({1,2},now,p));assert(!h.Capture({2,1},now,p));h.Commit();
 h.Begin(true);assert(!h.Capture({1,2},now,p));h.Commit();
}

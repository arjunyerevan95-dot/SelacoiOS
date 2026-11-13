#include "i_motion_sprite_runtime.h"
#include <cassert>
using namespace SelacoMotionRuntime;
int main(){
 int actor=0,tex=0; float uv[4]={0,1,0,1};
 float a[4][3]={{0,0,0},{1,0,0},{0,1,0},{1,1,0}};
 Begin(true);assert(!Capture(&actor,&tex,uv,a).valid());Commit();
 a[0][0]=3;Begin(false);auto r=Capture(&actor,&tex,uv,a);
 assert(r.valid()&&r.previousWorldVertices[0].x==0);Commit();
 auto old=Generation(&actor);Forget(&actor);assert(Generation(&actor)!=old);
 Begin(false);assert(!Capture(&actor,&tex,uv,a).valid());Commit();
 Begin(false);assert(Capture(&actor,&tex,uv,a).valid());Reject();assert(Get().rejected);
 assert(!Capture(&actor,&tex,uv,a).valid());assert(!Unambiguous());Commit();
 Begin(true);assert(!Capture(&actor,&tex,uv,a).valid());Commit();Forget(&actor);
}

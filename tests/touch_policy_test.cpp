#include "i_touch_policy.h"
#include <cassert>
int main(){using namespace SelacoIOS;AltLatch a;
 assert(a.press(1));assert(!a.release(1.05));assert(a.press(1.2));assert(a.latched);assert(a.release(1.25));
 assert(!a.press(2));assert(!a.latched);assert(!a.release(2.1));assert(a.press(3));assert(!a.release(3.6));assert(a.press(3.7));assert(!a.latched);a.reset();assert(!a.latched);
 assert(RadialSector(0,-100,32,140,8)==0);assert(RadialSector(100,0,32,140,8)==2);assert(RadialSector(0,0,32,140,8)==-1);assert(RadialSector(200,0,32,140,8)==-1);
 assert(StickAxis(.05,.05,.1,1)==0);assert(StickAxis(1,1,.1,1)==1);
}

#include "i_touch_math.h"
#include <cassert>
#include <limits>
int main(){
 using namespace SelacoIOS;
 auto a=GyroAxes(2,3,false,false,false);assert(a.x==2&&a.y==-3);
 a=GyroAxes(2,3,true,false,false);assert(a.x==-2&&a.y==3);
 a=GyroAxes(2,3,false,true,false);assert(a.x==-2&&a.y==-3);
 a=GyroAxes(2,3,false,false,true);assert(a.x==2&&a.y==3);
 assert(RenderPixels(874,3,.5)==1311);assert(RenderPixels(402,3,.5)==603);
 assert(RenderPixels(874,3,.33)==865);assert(RenderPixels(402,3,.33)==397);
 assert(RenderScale(0)==.5&&RenderScale(1)==.5&&RenderScale(std::numeric_limits<double>::quiet_NaN())==.5);
 assert(RenderPixels(-1,3,.5)==1);
}

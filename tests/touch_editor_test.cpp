#include "../overlays/gzselaco-ios/i_touch_editor.h"
#include <cassert>
#include <limits>
using G=SelacoIOS::EditorGesture;
int main(){G g;assert(!g.begin(1,10,10,-1,60));assert(g.begin(1,10,10,3,60));assert(g.control==3);assert(g.move(1,20,20)==G::Change::Drag);
 assert(g.begin(2,80,20,7,120));assert(g.control==3);assert(!g.begin(3,100,20,1,50));assert(g.move(2,140,20)==G::Change::Resize);assert(g.size==120);
 g.move(2,1000,20);assert(g.size==140);g.move(2,21,20);assert(g.size==44);
 g.end(1);assert(g.draining);assert(g.move(2,40,40)==G::Change::None);assert(!g.begin(3,50,50,2,60));g.end(2);assert(!g.first&&!g.second&&!g.draining);
 assert(g.begin(4,10,10,1,60));assert(g.begin(5,10,10,-1,0));g.move(5,11,10);assert(g.size==44);g.reset();assert(g.control==-1);
 assert(!g.begin(4,std::numeric_limits<double>::quiet_NaN(),0,1,60));assert(g.begin(6,0,0,1,999));assert(g.size==140);g.end(6);assert(g.control==-1);
 assert(g.begin(7,0,0,2,60));assert(g.begin(8,60,0,-1,0));g.end(8);assert(g.draining);assert(g.move(7,30,0)==G::Change::None);g.end(7);assert(!g.draining);
}

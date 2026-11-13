#include "i_touch_input.h"
#include "d_eventbase.h"
#include "i_interface.h"
#include "m_joy.h"
#include "c_bind.h"
#include <cassert>
#include <thread>
#include <limits>
FKeyBindings Bindings;
void Joy_GenerateButtonEvents(int old,int next,int count,int base){for(int i=0;i<count;i++)if((old^next)&(1<<i)){event_t e{};e.type=(next&(1<<i))?EV_KeyDown:EV_KeyUp;e.data1=base+i;D_PostEvent(&e);}}
static bool menu=false;static bool capture(){return menu;}Callbacks sysCallbacks{capture};
std::vector<event_t> events;int mx=0,my=0;
void D_PostEvent(event_t*e){events.push_back(*e);}void PostMouseMove(int x,int y){mx+=x;my+=y;}
int main(){Bindings.values={{0x1bf,"+attack"},{0x1c0,"+jump"}};SelacoTouchDrain();assert(!SelacoTouchMenu());
 SelacoTouchMove(5,-5);float axes[5]{};SelacoTouchAxes(axes);assert(axes[2]==1&&axes[3]==-1);
 SelacoTouchKey(0x100,true);SelacoTouchDrain();assert(events.back().type==EV_KeyDown&&events.back().data1==0x1bf);Bindings.values[0x1bf]="+use";SelacoTouchKey(0x100,false);SelacoTouchDrain();assert(events.back().type==EV_KeyUp&&events.back().data1==0x1bf);Bindings.values[0x1bf]="+attack";
 SelacoTouchKey(0x39,true);SelacoTouchKey(0x39,false);auto count=events.size();SelacoTouchDrain();assert(events.size()==count+1&&events.back().type==EV_KeyDown);SelacoTouchDrain();assert(events.size()==count+2&&events.back().type==EV_KeyUp);
 SelacoTouchLook(.4,.4);SelacoTouchDrain();assert(mx==0);SelacoTouchLook(.7,.7);SelacoTouchDrain();assert(mx==1&&my==1);
 SelacoTouchLook(std::numeric_limits<double>::infinity(),0);SelacoTouchDrain();assert(mx==1);
 SelacoTouchKey(0x100,true);SelacoTouchDrain();menu=true;SelacoTouchDrain();assert(events.back().type==EV_KeyUp);SelacoTouchLook(20,20);SelacoTouchDrain();assert(mx==1);
 SelacoTouchPulse(0x1c);SelacoTouchDrain();assert(events.back().type==EV_GUI_Event&&events.back().data1==13);
 SelacoTouchPulse(0x0f);SelacoTouchDrain();assert(events.back().data1==27);SelacoTouchPulse(0x3a);SelacoTouchDrain();assert(events.back().data1==27);
 SelacoTouchReset();menu=false;SelacoTouchDrain();std::thread t([]{for(int i=0;i<10000;i++){SelacoTouchLook(.1,.1);SelacoTouchMove(.5,-.5);}});for(int i=0;i<10000;i++)SelacoTouchDrain();t.join();SelacoTouchReset();SelacoTouchDrain();float z[5]{};SelacoTouchAxes(z);assert(z[2]==0&&z[3]==0);
}

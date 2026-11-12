#pragma once
#include <cstdint>
struct event_t {uint8_t type=0,subtype=0;int16_t data1=0,data2=0,data3=0;float x=0,y=0;};
enum {EV_KeyDown=1,EV_KeyUp,EV_GUI_Event,EV_GUI_KeyDown,EV_GUI_KeyUp,GK_UP=11,GK_DOWN=10,GK_LEFT=5,GK_RIGHT=6,GK_RETURN=13};
void D_PostEvent(event_t*);void PostMouseMove(int,int);

#include "i_touch_input.h"
#include "d_eventbase.h"
#include "i_interface.h"
#include "m_joy.h"
#include "keydef.h"
SelacoTouchState selacoTouch;
void SelacoTouchKey(int k,bool down){if(k<0||k>=512)return;std::lock_guard<std::mutex> l(selacoTouch.mutex);if(down&&!selacoTouch.keys[k])selacoTouch.pressed[k]=true;selacoTouch.keys[k]=down;}
void SelacoTouchPulse(int k){if(k<0||k>=512)return;std::lock_guard<std::mutex> l(selacoTouch.mutex);if(selacoTouch.pulses.size()<24)selacoTouch.pulses.push_back(k);}
void SelacoTouchLook(double x,double y){if(!std::isfinite(x)||!std::isfinite(y))return;std::lock_guard<std::mutex> l(selacoTouch.mutex);if(!selacoTouch.menu){selacoTouch.x=std::max(-2048.,std::min(2048.,selacoTouch.x+x));selacoTouch.y=std::max(-2048.,std::min(2048.,selacoTouch.y+y));}}
void SelacoTouchMove(double f,double s){std::lock_guard<std::mutex> l(selacoTouch.mutex);selacoTouch.forward=std::isfinite(f)?std::max(-1.,std::min(1.,f)):0;selacoTouch.side=std::isfinite(s)?std::max(-1.,std::min(1.,s)):0;}
void SelacoTouchReset(){std::lock_guard<std::mutex> l(selacoTouch.mutex);selacoTouch.clear();}
bool SelacoTouchMenu(){std::lock_guard<std::mutex> l(selacoTouch.mutex);return selacoTouch.menu;}
static int guiKey(int k){switch(k){case KEY_UPARROW:return GK_UP;case KEY_DOWNARROW:return GK_DOWN;case KEY_LEFTARROW:return GK_LEFT;case KEY_RIGHTARROW:return GK_RIGHT;case KEY_ENTER:return GK_RETURN;case KEY_ESCAPE:return 27;default:return 0;}}
static void post(int k,bool down,bool menu){event_t e{};if(menu){int g=guiKey(k);if(!g)return;e.type=EV_GUI_Event;e.subtype=down?EV_GUI_KeyDown:EV_GUI_KeyUp;e.data1=g;e.data2=g;}else{e.type=down?EV_KeyDown:EV_KeyUp;e.data1=k;}D_PostEvent(&e);}
void SelacoTouchDrain(){
 static bool sent[512]{};static bool previousMenu=true;
 bool mode=sysCallbacks.WantGuiCapture&&sysCallbacks.WantGuiCapture();
 bool keys[512]{};std::vector<int> pulses;int x=0,y=0;
 {std::lock_guard<std::mutex> l(selacoTouch.mutex);
  if(mode!=selacoTouch.menu){selacoTouch.clear();selacoTouch.menu=mode;}
  std::copy(std::begin(selacoTouch.keys),std::end(selacoTouch.keys),keys);pulses.swap(selacoTouch.pulses);
  for(int k=0;k<512;k++){if(selacoTouch.pressed[k]&&!keys[k]&&pulses.size()<24)pulses.push_back(k);selacoTouch.pressed[k]=false;}
  x=(int)selacoTouch.x;y=(int)selacoTouch.y;selacoTouch.x-=x;selacoTouch.y-=y;
 }
 if(mode!=previousMenu){for(int k=0;k<512;k++)if(sent[k]){post(k,false,previousMenu);sent[k]=false;}previousMenu=mode;}
 for(int k=0;k<512;k++)if(sent[k]!=keys[k]){post(k,keys[k],mode);sent[k]=keys[k];}
 for(int k:pulses){if(!sent[k]){post(k,true,mode);post(k,false,mode);}}
 if(!mode&&(x||y))PostMouseMove(x,y);
}
void SelacoTouchAxes(float *axes){std::lock_guard<std::mutex> l(selacoTouch.mutex);if(!selacoTouch.menu){axes[JOYAXIS_Forward]=(float)selacoTouch.forward;axes[JOYAXIS_Side]=(float)selacoTouch.side;}}

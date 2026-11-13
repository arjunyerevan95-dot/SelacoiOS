#pragma once
#include "i_touch_actions.h"
#include <cctype>
namespace SelacoIOS {
inline bool SameCommand(const char *a,const char *b) {
 if(!a||!b)return false;
 while(*a&&*b){if(std::tolower((unsigned char)*a++)!=std::tolower((unsigned char)*b++))return false;}
 return !*a&&!*b;
}
// Resolve loaded bindings on the engine thread. Never assume a physical key still
// performs its shipped action, and prefer the same PAD codes used by XInput/SDL.
template<class Binding> int ResolveTouchBinding(const TouchAction &a, Binding binding) {
 if(a.context!=TouchActionContext::Gameplay||!*a.defaultCommand)return a.scanCode;
 for(int k=0x1b4;k<=0x1c3;++k)if(SameCommand(binding(k),a.defaultCommand))return k;
 if(SameCommand(binding(a.scanCode),a.defaultCommand))return a.scanCode;
 for(int k=1;k<0x1c4;++k)if(SameCommand(binding(k),a.defaultCommand))return k;
 return -1; // Unbound is not permission to invoke an unrelated key or overwrite a binding.
}
}

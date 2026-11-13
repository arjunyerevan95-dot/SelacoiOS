#include "i_touch_binding.h"
#include <cassert>
#include <map>
#include <string>
int main(){using namespace SelacoIOS;std::map<int,std::string> b;
 auto get=[&](int k)->const char*{auto i=b.find(k);return i==b.end()?nullptr:i->second.c_str();};
 auto fire=FindTouchAction("fire");b[0x100]="+use";b[0x1bf]="+attack";
 assert(ResolveTouchBinding(*fire,get)==0x1bf);
 b[0x1bf]="+use";b[0x1bd]="+ATTACK";assert(ResolveTouchBinding(*fire,get)==0x1bd);
 b.erase(0x1bd);assert(ResolveTouchBinding(*fire,get)==-1);
 b[0x1c2]="+usereload";assert(ResolveTouchBinding(*FindTouchAction("use_reload"),get)==0x1c2);
 b[0x1c2]="+use";assert(ResolveTouchBinding(*FindTouchAction("use_reload"),get)==-1);
 b[0x13]="+reload";assert(ResolveTouchBinding(*FindTouchAction("reload"),get)==0x13);
 assert(ResolveTouchBinding(*FindTouchAction("confirm"),get)==0x1c);
}

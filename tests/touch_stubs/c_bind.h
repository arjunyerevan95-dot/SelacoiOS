#pragma once
#include <map>
#include <string>
struct FKeyBindings {std::map<int,std::string> values;const char *GetBind(int k)const{auto i=values.find(k);return i==values.end()?nullptr:i->second.c_str();}};
extern FKeyBindings Bindings;

#include "../overlays/gzselaco-ios/i_framegen_compare.h"
#include <cassert>
#include <thread>
int main(){
 SelacoCompare::SetEnabled(false);assert(!SelacoCompare::Enabled());
 SelacoCompare::SetEnabled(true);assert(SelacoCompare::Enabled());
 SelacoCompare::SetEnabled(false);SelacoCompare::Render();assert(SelacoCompare::rendered==1);assert(SelacoCompare::encoded==0);
 std::thread t([]{for(int i=0;i<10000;++i){SelacoCompare::Render();SelacoCompare::Encode();}});
 for(int i=0;i<10000;++i)SelacoCompare::SetEnabled(i%2);t.join();
 assert(SelacoCompare::rendered==10001);assert(SelacoCompare::encoded==10000);
}

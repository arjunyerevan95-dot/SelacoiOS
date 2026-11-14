#include "../overlays/gzselaco-ios/i_metalfx_retry.h"
#include <cassert>
#include <limits>
int main(){
 IOSMetalFXCreateRetry r;IOSMetalFXCreateKey k{1,2,640,360,1280,720,false};
 assert(r.Allow(k,0));r.Failed(0);
 assert(!r.Allow(k,499999999));assert(r.Allow(k,500000000));r.Failed(500000000);
 assert(!r.Allow(k,1499999999));assert(r.Allow(k,1500000000));r.Failed(1500000000);
 assert(!r.Allow(k,3499999999));assert(r.Allow(k,3500000000));r.Failed(3500000000);
 assert(!r.Allow(k,7499999999));assert(r.Allow(k,7500000000));r.Failed(7500000000);
 assert(!r.Allow(k,11499999999ULL));assert(r.Allow(k,11500000000ULL));
 r.Succeeded();assert(r.Allow(k,11500000001ULL));r.Failed(11500000001ULL);
 auto changed=k;changed.width++;assert(r.Allow(changed,11500000002ULL));r.Failed(11500000002ULL);
 changed.device++;assert(r.Allow(changed,11500000003ULL));r.Failed(11500000003ULL);
 changed.interpolation=true;assert(r.Allow(changed,11500000004ULL));r.Failed(11500000004ULL);
 assert(r.Allow(changed,0)); // Defensive monotonic-clock restart.
 r.Failed(std::numeric_limits<std::uint64_t>::max()-20);
 assert(!r.Allow(changed,std::numeric_limits<std::uint64_t>::max()));
 // Every material key field independently permits a fresh attempt.
 for(unsigned field=0;field<7;field++){
  IOSMetalFXCreateRetry gate;auto alt=k;assert(gate.Allow(k,100));gate.Failed(100);
  switch(field){case 0:alt.owner++;break;case 1:alt.device++;break;case 2:alt.width++;break;
   case 3:alt.height++;break;case 4:alt.outputWidth++;break;case 5:alt.outputHeight++;break;
   case 6:alt.interpolation=true;break;}
  assert(gate.Allow(alt,101));
 }
 IOSMetalFXCreateRetry sustained;unsigned attempts=0;
 for(std::uint64_t n=0;n<600;n++){auto now=n*16666667ULL;if(sustained.Allow(k,now)){attempts++;sustained.Failed(now);}}
 assert(attempts==5); // 600 failed-frame opportunities become 5 creation attempts.
}

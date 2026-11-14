#include "i_metalfx_event_validation.h"
#include <cassert>
int main(){int a=0,b=0;
assert(IOSMetalFXSharedEventDeviceCompatible(nullptr,&a));
assert(IOSMetalFXSharedEventDeviceCompatible(&a,&a));
assert(!IOSMetalFXSharedEventDeviceCompatible(&b,&a));
assert(!IOSMetalFXSharedEventDeviceCompatible(nullptr,nullptr));
assert(!IOSMetalFXSharedEventDeviceCompatible(&a,nullptr));
int q=0,r=0,d=0;
assert(IOSMetalFXExportObjectsValid(&a,&q,&a,&r,&d,nullptr,nullptr));
assert(IOSMetalFXExportObjectsValid(&a,&q,&a,&r,&d,&a,&a));
assert(!IOSMetalFXExportObjectsValid(nullptr,&q,&a,&r,&d,nullptr,nullptr));
assert(!IOSMetalFXExportObjectsValid(&a,nullptr,&a,&r,&d,nullptr,nullptr));
assert(!IOSMetalFXExportObjectsValid(&a,&q,&b,&r,&d,nullptr,nullptr));
assert(!IOSMetalFXExportObjectsValid(&a,&q,&a,nullptr,&d,nullptr,nullptr));
assert(!IOSMetalFXExportObjectsValid(&a,&q,&a,&r,nullptr,nullptr,nullptr));
assert(!IOSMetalFXExportObjectsValid(&a,&q,&a,&r,&r,nullptr,nullptr));
assert(!IOSMetalFXExportObjectsValid(&a,&q,&a,&r,&d,&b,nullptr));
assert(!IOSMetalFXExportObjectsValid(&a,&q,&a,&r,&d,nullptr,&b));
}

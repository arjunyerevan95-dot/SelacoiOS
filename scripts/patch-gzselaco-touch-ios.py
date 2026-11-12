#!/usr/bin/env python3
from pathlib import Path
import shutil,sys
root=Path(sys.argv[1]);repo=Path(__file__).resolve().parents[1]
ios=root/'src/common/platform/ios';cmake=root/'src/CMakeLists.txt';runtime=ios/'i_platform_runtime.mm'
for name in ['i_touch_actions.h','i_touch_policy.h','i_touch_math.h','i_touch_input.h','i_touch_input.cpp','i_touch_view.mm','i_title_menu_closure.cpp']:
 shutil.copyfile(repo/'overlays/gzselaco-ios'/name,ios/name)
s=cmake.read_text();old='\tcommon/platform/ios/i_title_menu_closure.cpp )';assert s.count(old)==1
s=s.replace(old,'\tcommon/platform/ios/i_title_menu_closure.cpp\n\tcommon/platform/ios/i_touch_input.cpp\n\tcommon/platform/ios/i_touch_view.mm )');s=s.replace('-framework IOSurface"','-framework IOSurface -framework CoreMotion"');s += '\nset_source_files_properties(common/platform/ios/i_touch_view.mm PROPERTIES COMPILE_FLAGS "-fobjc-arc")\n'
cmake.write_text(s)
s=runtime.read_text();s='#include "i_touch_input.h"\n'+s
old='    WriteBreadcrumb(@"phase=m2_view_loaded");';assert s.count(old)==1
s=s.replace(old,'    [root addSubview:SelacoCreateTouchView(self)];\n'+old);runtime.write_text(s)

#!/usr/bin/env python3
"""Compile the isolated native MetalFX modules after the existing touch patch.
Does not enable MetalFX. Runtime insertion/presentation must be separately wired.
"""
from pathlib import Path
import shutil,sys
root=Path(sys.argv[1]);repo=Path(__file__).resolve().parents[1]
cmake=root/'src/CMakeLists.txt';s=cmake.read_text()
old='\tcommon/platform/ios/i_touch_view.mm )'
assert s.count(old)==1, 'Run existing iOS touch patch first; exact CMake anchor missing'
s=s.replace(old,'\tcommon/platform/ios/i_metalfx_bridge.mm\n\tcommon/platform/ios/i_metalfx_interop.mm\n\tcommon/platform/ios/i_touch_view.mm )')
# Weak linkage preserves launch compatibility on systems without MetalFX.
old='-framework CoreMotion"'
assert s.count(old)==1, 'Expected iOS framework linker anchor'
s=s.replace(old,'-framework CoreMotion -weak_framework MetalFX"')
s+='\nset_source_files_properties(common/platform/ios/i_metalfx_bridge.mm common/platform/ios/i_metalfx_interop.mm PROPERTIES COMPILE_FLAGS "-fobjc-arc")\n'
ios=root/'src/common/platform/ios';ios.mkdir(parents=True,exist_ok=True)
for name in ['i_metalfx_bridge.h','i_metalfx_bridge.mm','i_metalfx_interop.h','i_metalfx_event_validation.h','i_metalfx_interop.mm',
             'i_metalfx_retry.h','i_temporal_history.h','i_temporal_primitive_history.h','RTGL-MIT-LICENSE.txt']:
    shutil.copyfile(repo/'overlays/gzselaco-ios'/name,ios/name)
cmake.write_text(s)
print('MetalFX bridge/interop compiled-in sources configured; runtime remains disabled')

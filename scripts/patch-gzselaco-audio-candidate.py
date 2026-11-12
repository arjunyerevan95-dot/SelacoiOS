#!/usr/bin/env python3
"""Opt-in audio source integration after build22 patches. Not shipped."""
from pathlib import Path
import shutil,sys
root=Path(sys.argv[1]);repo=Path(__file__).resolve().parents[1]
ios=root/'src/common/platform/ios'
shutil.copyfile(repo/'overlays/gzselaco-ios/i_audio_session.mm',ios/'i_audio_session.mm')
p=root/'src/CMakeLists.txt';s=p.read_text()
old='\tcommon/platform/ios/i_touch_view.mm )';assert s.count(old)==1
s=s.replace(old,'\tcommon/platform/ios/i_touch_view.mm\n\tcommon/platform/ios/i_audio_session.mm )')
old='-framework AudioUnit -framework CoreAudio -framework ApplicationServices -framework AudioToolbox -framework CoreFoundation'
assert s.count(old)==1
s=s.replace(old,'-framework CoreAudio -framework AudioToolbox -framework CoreFoundation -framework AVFAudio')
s+='\nset_source_files_properties(common/platform/ios/i_audio_session.mm PROPERTIES COMPILE_FLAGS "-fobjc-arc")\nadd_definitions(-DAL_LIBTYPE_STATIC)\n'
p.write_text(s)
p=ios/'i_platform_runtime.mm';s=p.read_text();s='extern "C" void SelacoAudioStart();\n'+s
old='    [root addSubview:SelacoCreateTouchView(self)];';assert s.count(old)==1
s=s.replace(old,old+'\n    SelacoAudioStart();')
for flag in ['-nosound','-nomusic']:
 old='            "'+flag+'",\n';assert s.count(old)==1;s=s.replace(old,'')
p.write_text(s)
p=ios/'i_title_menu_closure.cpp';s=p.read_text();s='extern "C" void SelacoAudioDrain();\n'+s
old='    SelacoTouchDrain();';assert s.count(old)==1;s=s.replace(old,old+'\n    SelacoAudioDrain();');p.write_text(s)

import subprocess
subprocess.run([sys.executable,str(repo/"scripts/patch-gzselaco-audio-diagnostics.py"),str(root)],check=True)

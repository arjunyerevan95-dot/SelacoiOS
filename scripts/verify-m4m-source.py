#!/usr/bin/env python3
"""Offline source-level regression checks; not a compile or device test."""
from pathlib import Path
import sys
r=Path(sys.argv[1])
def need(file, *markers):
    text=(r/file).read_text()
    for marker in markers:
        assert marker in text, (file,marker)
    return text
need('wadsrc/static/zscript/engine/ui/menu/loadsavemenu.zs', 'native readonly int saveDate, elapsedTime, levelNum;', 'native int saveFlags;', 'native void DoSave(int Selected, String savegamestring, int flags = 0);')
need('wadsrc/static/zscript/events.zs','GetSavegameFlags(bool quicksave, bool autosave)','GetSavegameTitle(int type)')
need('src/common/menu/savegamemanager.cpp',*[f'DEFINE_FIELD(FSaveGameNode, {x});' for x in ['saveDate','saveFlags','elapsedTime','levelNum']])
for file, signatures in {
 'src/common/menu/savegamemanager.cpp':['void FSavegameManagerBase::DoSave('],
 'src/g_game.cpp':['void G_SaveGame (','void G_DoSaveGame ('],
}.items():
 text=(r/file).read_text()
 for sig in signatures:
  body=text[text.index('{',text.index(sig))+1:]
  assert body.startswith('\n\tPrintf("SELACO_IOS_M4M_SAVE_BLOCKED write_attempted=0\\n");\n\treturn;'), sig
for file in ['wadsrc/static/zscript/compatibility.zs','src/common/menu/savegamemanager.cpp','src/events.cpp']:
 text=(r/file).read_text()
 assert 'SELACO_IOS_M4K_COMPAT' not in text
 assert 'SelacoIOSM4JDoSaveDiagnostic' not in text
print('PASS: upstream native contracts, unmodified signatures, immediate no-write guards, no guessed compatibility')

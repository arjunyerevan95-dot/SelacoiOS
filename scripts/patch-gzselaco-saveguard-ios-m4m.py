#!/usr/bin/env python3
"""Keep the upstream API intact, but refuse writes in this title-menu experiment."""
from pathlib import Path
import sys
root = Path(sys.argv[1])
for name, signatures in {
    'src/common/menu/savegamemanager.cpp': [
        'void FSavegameManagerBase::DoSave(int Selected, const char *savegamestring, int flags)'],
    'src/g_game.cpp': [
        'void G_SaveGame (const char *filename, const char *description, int flags)',
        'void G_DoSaveGame (bool okForQuicksave, bool forceQuicksave, FString filename, const char *description, int32_t flags)'],
}.items():
    p = root / name
    text = p.read_text()
    for signature in signatures:
        anchor = signature + '\n{\n'
        if text.count(anchor) != 1:
            raise RuntimeError(f'upstream save boundary changed: {signature}')
        text = text.replace(anchor, anchor + '\tPrintf("SELACO_IOS_M4M_SAVE_BLOCKED write_attempted=0\\n");\n\treturn;\n', 1)
    p.write_text(text)

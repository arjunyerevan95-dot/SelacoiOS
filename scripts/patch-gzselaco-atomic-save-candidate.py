#!/usr/bin/env python3
"""Opt-in candidate; NOT invoked by the shipped build pipeline.
Apply to the fully materialized build22 source tree only. Device roundtrip required.
"""
from pathlib import Path
import shutil,sys
root=Path(sys.argv[1]); repo=Path(__file__).resolve().parents[1]
guard='\tPrintf("SELACO_IOS_M4M_SAVE_BLOCKED write_attempted=0\\n");\n\treturn;\n'
paths=[root/'src/g_game.cpp',root/'src/common/menu/savegamemanager.cpp']
texts=[p.read_text() for p in paths]
assert texts[0].count(guard)==2 and texts[1].count(guard)==1, 'expected no-write base'
old='''\tbool succeeded = false;

\tif (WriteZip(filename.GetChars(), savegame_content.Data(), savegame_content.Size()))
\t{
\t\t// Check whether the file is ok by trying to open it.
\t\tFResourceFile *test = FResourceFile::OpenResourceFile(filename.GetChars(), true);
\t\tif (test != nullptr)
\t\t{
\t\t\tdelete test;
\t\t\tsucceeded = true;
\t\t}
\t}'''
new='''\tstd::string leaf = SelacoIOS::SaveLeaf(filename.GetChars());
\tif (!leaf.empty()) filename = G_BuildSaveName(leaf.c_str());
\tbool succeeded = !leaf.empty() && SelacoIOS::AtomicSave(filename.GetChars(),
\t\t[&](const char *staging) {
\t\t\treturn WriteZip(staging, savegame_content.Data(), savegame_content.Size());
\t\t},
\t\t[](const char *staging) {
\t\t\tFResourceFile *test = FResourceFile::OpenResourceFile(staging, true);
\t\t\tif (!test) return false;
\t\t\tdelete test;
\t\t\treturn true;
\t\t});'''
assert texts[0].count(old)==1, 'save serialization boundary changed'
texts[0]='#include "common/platform/ios/i_atomic_save.h"\n'+texts[0].replace(old,new)
shutil.copyfile(repo/'overlays/gzselaco-ios/i_atomic_save.h',root/'src/common/platform/ios/i_atomic_save.h')
for p,s in zip(paths,texts):p.write_text(s.replace(guard,''))
print('Atomic save candidate staged; engine ZIP-open validation is NOT a device load roundtrip.')

p=root/'src/common/platform/ios/i_platform_runtime.mm'
s=p.read_text();old='return DocumentsPath("Savegames", true);'
assert s.count(old)==1
p.write_text(s.replace(old,'return DocumentsPath("Savegames-candidate", true);'))

s=p.read_text();anchor='        // Optional, exact allowlisted private mod only. Never enumerate Mods.'
assert s.count(anchor)==1
s=s.replace(anchor,'        arguments.emplace_back("-savedir");\n        arguments.emplace_back([DiagnosticDirectory() stringByAppendingPathComponent:@"Savegames-candidate"].fileSystemRepresentation);\n'+anchor)
p.write_text(s)

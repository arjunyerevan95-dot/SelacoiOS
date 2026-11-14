#!/usr/bin/env python3
"""Match fd4b0b60d8 WeaponSprite TopSprite compatibility-marker semantics."""
from pathlib import Path
import sys

OLD = '''\t\t\t\t\telse
\t\t\t\t\t{
\t\t\t\t\t\tsc.ScriptError("Unknown WeaponSprite property '%s'", sc.String);
\t\t\t\t\t}'''
NEW = '''\t\t\t\t\telse if (sc.Compare("TopSprite"))
\t\t\t\t\t{
\t\t\t\t\t\t// v0.200 fd4b0b60d8: valueless compatibility marker.
\t\t\t\t\t\t// Reference parser advances directly to its next property.
\t\t\t\t\t}
''' + OLD

def transform(source):
    if NEW in source:
        return source
    if source.count(OLD) != 1:
        raise RuntimeError("WeaponSprite parser anchor changed; refusing broad replacement")
    return source.replace(OLD, NEW, 1)

if __name__ == "__main__":
    p = Path(sys.argv[1]) / "src/common/textures/texturemanager.cpp"
    p.write_text(transform(p.read_text()))
    print("PASS: TopSprite valueless marker matched; unknown-property errors retained")

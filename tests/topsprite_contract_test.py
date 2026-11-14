#!/usr/bin/env python3
"""Targeted source-contract checks; no retail data required."""
import importlib.util
from pathlib import Path
import sys
repo=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("patch",repo/"scripts/patch-gzselaco-topsprite.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
original="prefix\n"+m.OLD+"\nsuffix"
patched=m.transform(original)
assert patched.count('sc.Compare("TopSprite")')==1
assert patched.count('sc.ScriptError("Unknown WeaponSprite property')==1
assert patched.replace(m.NEW,m.OLD)==original
body=patched.split('sc.Compare("TopSprite")',1)[1].split("else",1)[0]
assert "MustGet" not in body and "sc.Float" not in body and "sc.Number" not in body
assert m.transform(patched)==patched
for bad in ("",m.OLD+m.OLD):
    try: m.transform(bad)
    except RuntimeError: pass
    else: raise AssertionError("Unexpected source was accepted")
if len(sys.argv)>1:
    p=Path(sys.argv[1])/"src/common/textures/texturemanager.cpp"
    real=p.read_text()
    assert m.NEW in real
    assert real.count('sc.Compare("TopSprite")')==1
print("PASS TopSprite: valueless branch; unknown errors retained; idempotent; exact-anchor guards")

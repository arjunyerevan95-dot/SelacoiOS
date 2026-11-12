#!/usr/bin/env python3
"""Bounded diagnostics for device-only level-transition silence; no forced unpause."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
def edit(rel,old,new):
 p=root/rel;s=p.read_text();assert s.count(old)==1,(rel,old[:50]);p.write_text(s.replace(old,new))
p='src/common/audio/sound/oalsound.cpp'
a='void OpenALSoundRenderer::SetInactive(SoundRenderer::EInactiveState state)\n{'
edit(p,a,a+'''\n    static int last = -1;
    if ((int)state != last) { Printf("iOS OpenAL inactive-state=%d\\n", (int)state); last = (int)state; }''')
p='src/common/audio/sound/s_sound.cpp'
a='void S_PauseSound(bool notmusic, bool notsfx)\n{'
edit(p,a,a+'''\n    static unsigned count = 0;
    if (count++ < 24) Printf("iOS audio pause music=%d sfx=%d state=%d paused=%d external=%d\\n", !notmusic, !notsfx, (int)gamestate, (int)paused, (int)pauseext);''')
a='void S_ResumeSound(bool notsfx)\n{'
edit(p,a,a+'''\n    static unsigned count = 0;
    if (count++ < 24) Printf("iOS audio resume sfx=%d state=%d paused=%d external=%d\\n", !notsfx, (int)gamestate, (int)paused, (int)pauseext);''')

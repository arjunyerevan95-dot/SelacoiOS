#!/usr/bin/env python3
"""Apply experimental temporal stack AFTER existing iOS/touch/scene/present patches.
Not part of default controls builds; runtime remains separately opt-in.
"""
from pathlib import Path
import subprocess,sys
repo=Path(__file__).resolve().parents[1];root=Path(sys.argv[1]).resolve()
patches=[
 'patch-gzselaco-metalfx-native.py',
 'patch-gzselaco-metalfx-device.py',
 'patch-gzselaco-metalfx-present.py',
 'patch-gzselaco-temporal-motion.py',
 'patch-gzselaco-temporal-sprites.py',
 'patch-gzselaco-temporal-views.py',
 'patch-gzselaco-temporal-models.py',
 'patch-gzselaco-temporal-world-guards.py',
 'patch-gzselaco-temporal-reactive-jitter.py',
 'patch-gzselaco-metalfx-consume.py',
 'patch-gzselaco-temporal-candidate.py',
 'patch-gzselaco-temporal-fallback.py',
 'patch-gzselaco-early-frame-limit.py',
 'patch-gzselaco-metalfx-pair-present.py',
 'patch-gzselaco-metalfx-composition.py',
 'patch-gzselaco-metalfx-framegen-route.py',
 'patch-gzselaco-ios-output-transition.py',
 'patch-gzselaco-metalfx-test-launcher.py',
]
for name in patches:
 subprocess.run([sys.executable,str(repo/'scripts'/name),str(root)],check=True)
print('Experimental MetalFX stack materialized; no full-coverage/device claim')

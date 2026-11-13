#!/usr/bin/env python3
"""Experimental test action only; never advertise framegen before renderer routing."""
from pathlib import Path
import sys
p=Path(sys.argv[1])/'src/common/platform/ios/i_platform_runtime.mm';s=p.read_text()
a='    choice.preferredAction = balanced;'
assert s.count(a)==1
s=s.replace(a,'''    [choice addAction:[UIAlertAction actionWithTitle:@"Test MetalFX temporal (experimental)"
        style:UIAlertActionStyleDefault handler:^(UIAlertAction *action) {
            (void)action; self.renderScale = .5;
            setenv("SELACO_IOS_METALFX", "1", 1);
            setenv("SELACO_MOTION_DIAGNOSTIC", "1", 1);
            setenv("SELACO_TEMPORAL_JITTER", "1", 1);
            setenv("SELACO_TEMPORAL_SUPPORTED_FRAMES", "1", 1);
            setenv("SELACO_IOS_EARLY_LIMIT", "1", 1);
            unsetenv("SELACO_IOS_METALFX_FRAMEGEN");
            WriteBreadcrumb(@"experimental_temporal_requested_framegen_disabled");
            [self beginEngine];
        }]];
'''+a)
p.write_text(s)
print('Experimental temporal test action added; framegen remains unavailable')

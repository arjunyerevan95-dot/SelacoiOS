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
a='    choice.preferredAction = balanced;'
s=s.replace(a,'''    if (@available(iOS 26.0, *)) {
        [choice addAction:[UIAlertAction actionWithTitle:@"Test temporal + framegen (VSync on, SDR)"
            style:UIAlertActionStyleDefault handler:^(UIAlertAction *action) {
                (void)action; self.renderScale=.5;
                setenv("SELACO_IOS_METALFX","1",1);
                setenv("SELACO_MOTION_DIAGNOSTIC","1",1);
                setenv("SELACO_TEMPORAL_JITTER","1",1);
                setenv("SELACO_TEMPORAL_SUPPORTED_FRAMES","1",1);
                setenv("SELACO_IOS_EARLY_LIMIT","1",1);
                setenv("SELACO_IOS_METALFX_FRAMEGEN","1",1);
                WriteBreadcrumb(@"experimental_framegen_requested_runtime_support_not_verified");
                [self beginEngine];
            }]];
    }
'''+a)
anchor='        std::vector<char *> argv;'
assert s.count(anchor)==1
s=s.replace(anchor,'''        const char* fgRequest=std::getenv("SELACO_IOS_METALFX_FRAMEGEN");
        if(fgRequest && !std::strcmp(fgRequest,"1")) {
            arguments.emplace_back("+vid_maxfps");arguments.emplace_back("60");
            arguments.emplace_back("+vk_hdr");arguments.emplace_back("0");
        }
'''+anchor)
s=s.replace('#include \"m_argv.h\"','#include \"m_argv.h\"\n#include <cstring>\n#include <cstdlib>')
p.write_text(s)
print('Experimental temporal and guarded iOS26 framegen test actions added')

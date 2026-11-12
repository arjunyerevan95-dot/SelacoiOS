#!/usr/bin/env python3
"""Present render-scale choice before any Metal/Vulkan or engine startup."""
from pathlib import Path
import sys
p=Path(sys.argv[1])/'src/common/platform/ios/i_platform_runtime.mm';s=p.read_text()
s='#include "i_touch_math.h"\n'+s
old='@property(nonatomic, assign) BOOL initializationStarted;'
assert s.count(old)==1;s=s.replace(old,old+'\n@property(nonatomic, assign) BOOL launchChoiceShown;\n@property(nonatomic, assign) double renderScale;\n- (void)beginEngine;')
old='''    const CGSize pixels = CGSizeMake(points.width * scale, points.height * scale);'''
assert s.count(old)==1;s=s.replace(old,'''    const CGSize pixels = CGSizeMake(
        SelacoIOS::RenderPixels(points.width, scale, self.renderScale),
        SelacoIOS::RenderPixels(points.height, scale, self.renderScale));''')
old='''    [super viewDidAppear:animated];
    if (self.initializationStarted) {'''
new='''    [super viewDidAppear:animated];
    if (self.launchChoiceShown || self.initializationStarted) return;
    self.launchChoiceShown = YES;
    self.renderScale = .5;
    UIAlertController *choice = [UIAlertController alertControllerWithTitle:@"Selaco rendering"
        message:@"0.5× is the recommended default. Choose 0.33× for higher performance. Touch controls stay full size."
        preferredStyle:UIAlertControllerStyleAlert];
    UIAlertAction *balanced = [UIAlertAction actionWithTitle:@"Play at 0.5× (default)"
        style:UIAlertActionStyleDefault handler:^(UIAlertAction *action) {
            (void)action; self.renderScale = .5; [self beginEngine];
        }];
    [choice addAction:balanced];
    [choice addAction:[UIAlertAction actionWithTitle:@"Play at 0.33× (performance)"
        style:UIAlertActionStyleDefault handler:^(UIAlertAction *action) {
            (void)action; self.renderScale = .33; [self beginEngine];
        }]];
    choice.preferredAction = balanced;
    [self presentViewController:choice animated:YES completion:nil];
}

- (void)beginEngine
{
    if (self.initializationStarted) {'''
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace('    gRendererHandoffController = self;', '    WriteBreadcrumb([NSString stringWithFormat:@"render_scale_selected=%.2f", self.renderScale]);\n    gRendererHandoffController = self;')
p.write_text(s)

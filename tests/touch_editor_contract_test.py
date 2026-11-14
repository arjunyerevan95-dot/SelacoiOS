from pathlib import Path
r=Path(__file__).resolve().parents[1];s=(r/'overlays/gzselaco-ios/i_touch_view.mm').read_text()
assert 'if(_editing){[self editorTouchesBegan:ts];return;}' in s
assert 'if(_editing){[self editorTouchesMoved:ts];return;}' in s
assert 'if(_editing){for(UITouch*t in ts)_editGesture.end' in s
assert '- (void)reset{_editGesture.reset();' in s
assert '_editSize.minimumValue=44;_editSize.maximumValue=140;' in s
assert 'if(b.tag==1&&_snapshot)_settings=_snapshot;' in s
assert 'if(b.tag==0)[self save];' in s
assert '_layout[i][@"size"]=@(_editGesture.size)' in s
assert "'i_touch_editor.h'" in (r/'scripts/patch-gzselaco-touch-ios.py').read_text()
print('PASS editor owns begin/move/end before gameplay; cancel resets; slider and Save/Cancel retained')

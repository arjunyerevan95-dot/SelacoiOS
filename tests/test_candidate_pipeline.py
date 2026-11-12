#!/usr/bin/env python3
"""Materialize shell/Python driver transforms without Apple tooling or builds."""
from pathlib import Path
import os,subprocess,tempfile,unittest,shutil
REPO=Path(__file__).resolve().parents[1]
def transform(script,source,target,env):
 text=Path(script).read_text(); code=text.split("<<'PY'\n",1)[1].split('\nPY\n',1)[0]
 subprocess.run(['python3','-c',code,str(source),str(target)],check=True,env=env,cwd=REPO)
 subprocess.run(['bash','-n',str(target)],check=True)
class Pipeline(unittest.TestCase):
 def test_both_modes(self):
  for enabled in ['0','1']:
   env=dict(os.environ,SELACO_IOS_AUDIO_CANDIDATE=enabled,SELACO_IOS_SAVES_CANDIDATE=enabled)
   with tempfile.TemporaryDirectory() as d:
    d=Path(d)
    transform(REPO/'scripts/m4-title-menu-compile-probe.sh',REPO/'scripts/m0-full-engine-compile-probe.sh',d/'compile.sh',env)
    transform(d/'compile.sh',REPO/'scripts/m0-full-engine-configure-probe.sh',d/'configure.sh',env)
    config=(d/'configure.sh').read_text()
    self.assertLess(config.index('patch-gzselaco-touch-ios.py'),config.index('patch-gzselaco-audio-candidate.py'))
    self.assertIn('"${audio_cmake_args[@]}"',config)
    transform(REPO/'scripts/m4-title-menu-app-artifact-probe.sh',REPO/'scripts/m4-engine-init-app-artifact-probe.sh',d/'app.sh',env)
    app=(d/'app.sh').read_text();version='24' if enabled=='1' else '22'
    self.assertIn(f'"CFBundleVersion": "{version}"',app)
    self.assertIn('OPENAL-LICENSE.txt',app); self.assertIn('STB-VORBIS-LICENSE.txt',app)
 def test_opt_in_source_patches(self):
  base=REPO/'.codebase-memory-worktree/GZSelaco-controls-final'
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   for rel in ['src/g_game.cpp','src/common/menu/savegamemanager.cpp','src/CMakeLists.txt','src/common/platform/ios/i_platform_runtime.mm','src/common/platform/ios/i_title_menu_closure.cpp']:
    p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/rel,p)
   for script in ['patch-gzselaco-resolution-launcher.py','patch-gzselaco-audio-candidate.py','patch-gzselaco-atomic-save-candidate.py']:
    subprocess.run(['python3',str(REPO/'scripts'/script),d],check=True)
   runtime=(root/'src/common/platform/ios/i_platform_runtime.mm').read_text()
   self.assertNotIn('SelacoIOS::RenderPixels',runtime);self.assertIn('SELACO_IOS_SCENE_SCALE',runtime);self.assertIn('self.renderScale = .5',runtime);self.assertIn('self.renderScale = .33',runtime);self.assertIn('Savegames-candidate',runtime);self.assertNotIn('"-nosound"',runtime)
   self.assertIn('DocumentsPath("Savegames-candidate", true) + "/"',runtime)
   self.assertNotIn('WriteZip(filename.GetChars()', (root/'src/g_game.cpp').read_text())
   self.assertIn('"-nosound"',(base/'src/common/platform/ios/i_platform_runtime.mm').read_text())
if __name__=='__main__':unittest.main()

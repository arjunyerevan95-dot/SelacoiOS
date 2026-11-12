# Post-build22 candidate engineering (not shipped)

Build22 remains silent and no-write. No release workflow is changed here.

## Saves

`patch-gzselaco-atomic-save-candidate.py` is an explicit opt-in after the build22
patch chain. It replaces the direct final-file WriteZip with unique same-directory
staging, existing engine ZIP-open validation, file fsync, then atomic rename.
All three no-write guards are removed only in the opt-in tree. The destination
is never touched before successful validation/sync. The same-directory temporary
file is cleaned on ordinary failure and C++ exceptions. Process death can leave
a `.pending-*` file, not a partially overwritten old save. Cleanup of such files
is intentionally not automatic. File fsync is not a guarantee against every
power-loss case; parent-directory durability is not guaranteed.

Local portable production-helper tests cover partial writes, failed validation,
exceptions, successful replacement and fresh save, rename failure, missing
parent, null target, and temporary-file cleanup. Source-patch assertions pass
against exact build22 materialization. This does NOT validate retail game state
serialization. Required next: fresh on-device save/load roundtrip in disposable
save slot, restart and load, manual/autosave/quick-save selection checks. Keep
existing saves backed up before testing overwrite behavior.

## Audio

Official OpenAL Soft 1.24.3 is pinned by commit in OPENAL_CANDIDATE_PIN.env.
Its CoreAudio backend explicitly uses RemoteIO on iOS. The standalone dependency
script builds static arm64 with CoreAudio required, not silently substituted.
An opt-in source patch adds the audio-session unit and engine-thread drain; its application has been tested on a disposable build22 source copy. The release configure pipeline is not yet wired to the archive. Apple compilation has not been run.

Integration gates before enabling sound:
- NO_OPENAL=OFF, DYN_OPENAL=OFF, explicit include/archive; AL_LIBTYPE_STATIC.
- Replace engine's desktop-only ApplicationServices framework list on iOS with
  AudioToolbox/CoreAudio/CoreFoundation plus AVFAudio for app session ownership.
- Implemented candidate: AVAudioSession playback on main thread before engine startup.
- Implemented candidate: interruptions/background publish atomic desired state;
  I_StartTic applies SetInactive on the engine thread, using OpenAL device pause.
  Session reactivates before resume. Media-services reset fails silent until
  app restart; automatic device recreation remains future work. Route changes
  and interruption timing require device verification.
- Opt-in source patch removes -nosound/-nomusic. Never apply it without static
  backend configuration and required frameworks. Release remains silent.
- Test effect + music, mute/category behavior, wired/Bluetooth routing and
  interruption/background/foreground on device. ZMusic decoder availability
  still requires actual music playback test.
- Include OpenAL Soft license and pinned-source/relink information with release.

No runner or user-device writes are made by these local tests.

## Integrated build23 candidate

Workflow now explicitly opts into both candidate modes, version 0.9.3(23).
OpenAL has compiled in a Linux host check; a statically linked loopback test
produced nonzero PCM. This is not proof of iOS speaker output. Nested driver
transforms, source-patch assertions, touch bridge/math and atomic-save tests pass.

Experimental writes are isolated in Documents/Selaco/Savegames-candidate using
-savedir, and final write names are rebased to that directory. Existing save
files are neither moved nor overwritten. Device roundtrip remains required.

Launch UI selects 0.5x (default) or 0.33x physical drawable resolution. The Metal
layer and framebuffer use those same pixels, while UIKit controls continue using
unscaled points. Desktop window-size requests cannot override UIKit size.
Gyro defaults are reversed from build22 based on device feedback; horizontal
and vertical inversion are independently selectable in the scrollable settings.

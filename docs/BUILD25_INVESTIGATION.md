# Post-build24 investigation (not a delivered fix)

User: menu audio works; no audio after entering game. Turning VSync off causes brown/flashing output. Screenshot shows flat dark game output with intact UIKit controls. This confirms startup audio repair but not gameplay audio completion.

Device evidence attempt: paired discovery empty; usbmux briefly lists Network device, lockdown QueryType disconnects and device disappears before HouseArrest opens. No new logs obtained, no user data/settings/pairing changed. Await awake/unlocked phone or exported log. Determine whether audio loss occurs with VSync left ON from launch, independently of render failure.

Concrete renderer hazards found: swapchain reconfiguration destroys views/framebuffers without explicitly waiting for pending presentation; one binary render-finished semaphore is reused across all acquired images. Candidate adds device-idle only at reconfiguration and per-swapchain-image render-finished semaphores, reusable on image reacquisition. It does NOT force VSync or claim an FPS improvement. Exact-source ordering tests pass; GPU/device validation pending.

Bounded diagnostics prepared for audio session activation/interruption/reset, engine active/inactive gate, OpenAL listener inactive state and game pause/resume flags. No unconditional unpause, device reset or game-state changes. Original static Vorbis decoder remains. Short ALT label also fixes screenshot overflow.

No Mac build/publish yet for these changes. Icon pack kept private; requires separate safe packaging rather than public asset upload. Existing saves untouched.

## Authorized USB read completed
Read three known guest diagnostic files, service and lockdown closed. No writes. Fresh game log has repeated `Unsupported audio format: Mono/Stereo, (invalid sample type)`. Confirmed source mismatch: Float32 decoder vs Int16-only SFX consumer; changed decoder to Int16. Synthetic mono/stereo decoding, seeks/loops, real engine format-selector extraction and static OpenAL loopback now pass under ASan/UBSan. Render diagnostic confirms actual scene946x435 in native2868x1320 pipeline at0.33. Current log has VSync1 startup but no toggle event, so does not establish the flashing cause. Presentation candidate still requires device validation.

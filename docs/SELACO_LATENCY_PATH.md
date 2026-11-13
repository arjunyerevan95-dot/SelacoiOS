# Input-to-present latency audit

Pinned engine already calls I_StartTic and D_ProcessEvents immediately before
D_Display, and System_DispatchEvent applies local mouse view movement between
simulation ticks. Do not duplicate event pumping or claim the35Hz simulation
means mouse view updates are limited to35Hz.

Actual avoidable delay: VkCommandBufferManager::WaitForCommands calls FPSLimit
AFTER FlushCommands and BEFORE QueuePresent. The opt-in
patch-gzselaco-early-frame-limit.py moves that same cap wait to the start of the
D_DoomLoop frame, before I_SetFrameTime/simulation/input. It keeps existing cap
and menu rules, skips the late wait only when this exact frame used the early
wait, and leaves direct render/screenshot paths with the original fallback.
Enable only through SELACO_IOS_EARLY_LIMIT=1; default behavior unchanged.

This does not remove the full-frame fence retirement, increase queued frames,
change35Hz gameplay/network simulation, add another input pump, or claim latency
measurements. The eight-submit ring is not eight frames in flight: Update still
retires all submitted fences each frame. Removing that wait without redesigning
resource ownership would break deletion lists and temporal input lifetimes.

Validation: exact-source patch applies and source-order checks pass; main-engine
compilation and device A/B remain needed. The portable limiter's final2ms loop
still uses sleep_for(0); changing that separately trades battery against pacing
precision and has not been done blindly.

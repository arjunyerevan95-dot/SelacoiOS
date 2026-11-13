# Experimental actual frame interpolation route
Apply patch-gzselaco-metalfx-framegen-route.py after the temporal stack, paired
presentation lifecycle and clean/full composition patches. It copies the pacer
header into the engine. Runtime remains explicitly opt-in; no defaults change.

The route snapshots each eligible real-frame timestamp on the Core Animation
monotonic clock, validates consecutive serials, projection, strict world motion and
matched clean/full images, then invokes IOSMetalFXBackendInterpolate on actual
exportable images. HDR is excluded pending an EDR color-contract validation.

Successful encoding is not presentation. The generated image is copied into the
current pipeline, drawn into the acquired swapchain image and then replaced by the
exact saved real composite before final normal presentation. History/source/output
resources remain alive under the normal fence/timeline retirement.

The pacer reserves one pair only. A failure before acquisition cancels that specific
unsubmitted reservation; acquired/submitted work retains capacity until actual real
presentation feedback or explicit exceptional drain/generation invalidation. A late
encode is discarded for presentation rather than queueing a stale generated frame.
Bounded log reasons report unsupported timing/refresh, capture/projection/history,
HDR, cadence and native validation. First GPU submission and timed submission are
explicitly distinguished from visible device results.

Validation: patch materialized on full pinned-source fixture, source-order checks
passed, updated C++ pacer test compiled/ran on MSVC. Apple/full-engine compilation,
GPU interpolation output, presentation and visual quality remain unverified. The
conservative composite influence overlay repeats current background at translucent
weapon/HUD boundaries; synthetic-frame edge artifacts remain a known test target.

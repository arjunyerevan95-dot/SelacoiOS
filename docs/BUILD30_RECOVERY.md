# Build30 bounded recovery candidate

Base: build29 / 287c71455fb76df4c7bacb62754a24feb5bc5921.

Model: the renderer feeds strict motion/projection/color history into temporal
upscaling, then reserves one timed generated/real presentation pair. Current
30fps production was rejected by a previous 45+fps / 90+Hz admission guard.
Build29 device counters confirm ~30 renderer fps, blockedCadence on every frame,
zero captures/encodes/queued pairs. Motion becomes valid on some frames but
`temporal=0`, so cadence is not proof of the only remaining blocker.

Changes: allow supported 30-to-60 cadence with half-real-period spacing;
preserve fail-closed motion/coverage/HDR/timing/pending guards. Bounded native
backend failure markers and preflight masks distinguish unavailable Metal
interop/scaler from invalid motion/usage/output geometry. No framegen success
or latency reduction claim before device presentation feedback.

Touch: discoverable Edit controls button opens drag/resize mode with explicit
Save/Cancel; settings snapshot and selected native action are preserved. Slider
range matches actual renderer limits. Native binding receipts report requested,
resolved and effective action. Read-only device settings show v4 action IDs and
positions already correct, so resetting customized layout is not a fix.
Use/Reload's behavior remains unverified in-game; its native PAD hold/release
and simultaneous look route now have portable coverage. No binding overwritten.

Validation: exact pinned upstream offline worktree, cumulative iOS source
patches and MetalFX stack materialized; admission/route/composition contracts
pass. MSVC pacer (including 30->60 at 60/120Hz), binding, policy, input suites
pass. Native UIKit/Metal build and device behavior remain to be tested.
Audio and save implementations unchanged. No licensed game data included.

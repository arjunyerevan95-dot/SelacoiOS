# Build24 control candidate

The user reported build23 gyro working, no music or SFX, a colliding radial, and insufficient customization.

The control layer now uses the audited 65-action native key registry. Eight gameplay slots and eight menu slots have action, position, visibility, label, size and opacity settings. Main/secondary radial slots are individually assignable; weapon slots include all native number keys. Map and Codex are available in the default radial and menu layer. Native key remapping still changes the meaning of the matching key, as disclosed in the binding chooser.

The radial is an isolated modal wedge overlay, without underlying button circles. ALT quick double-tap latches the native +altattack action until tapped again; this is weapon-dependent and not a promise every weapon has ADS. Menu changes, background, cancellation, radial and settings release held inputs. A three-finger one-second hold provides recovery if buttons have been hidden.

Separate X/Y swipe and gyro gain, ADS/fire-drag multipliers, movement/look regions, stick radius/deadzone/response and radial center/diameter/hold threshold are configurable. Existing v1 gains/layout and gyro inversion are migrated without rewriting the original v1 preference. Apply saves v2; Cancel and Pause discard the editing snapshot. Reset affects controls only.

Strict C++ action/policy/math/input tests pass locally. UIKit compilation and visual/touch validation require the Apple build/device. No claim of on-device verification yet.

The save-directory separator fix keeps globals inside Savegames-candidate. Existing files are never deleted or overwritten by migration code (none added); old malformed globals paths remain intact. Device save/load roundtrip remains unverified.

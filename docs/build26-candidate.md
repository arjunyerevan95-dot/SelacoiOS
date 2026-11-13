# Build 26 candidate

Changes: approved compact touch layout (fire leftmost in combat cluster, combined Use/Reload, separate dash and radial); symbol glyphs; right empty-look double-tap toggles ADS independently of movement fingers. Custom layouts are preserved. Untouched original defaults migrate with a backup; customized installs can select the approved preset in touch settings.

Presentation: iOS VSync-off prefers supported MAILBOX. If unavailable, it uses FIFO and explicitly logs that this safety fallback is not uncapped. This is a stability candidate for the reported flashing/blank output, not proof of an unlocked-frame-rate fix.

Preserved: existing bundle identity, saves, Int16 audio fix and prior presentation resource retirement.

Evidence: focused gesture-policy test compiled and passed on Linux; exact presentation patch fixture passed against pinned engine 95130c3a8f8f746ea6412644571af4ee5de32366. Native iOS compilation is required. Device confirmation remains required for layout, simultaneous touch, ADS, gyro and presentation.

Known gap: this build does not replace the existing gameplay input backend with Windows XInput. Common native controller event support exists upstream, but full Selaco retail pad mappings and glyph behavior were not available in the source-only checkout. Do not describe the UI symbols as proof of in-game controller recognition.

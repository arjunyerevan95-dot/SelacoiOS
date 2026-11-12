# M4M upstream save API refresh

## Evidence and architectural model

The M4H device evidence records successful Vulkan creation on A18 Pro and
21,447 indexed textures, then 24 fatal retail ZScript errors. This is not evidence
of a graphics hang. M4K placed guessed fields on Object, which was invalid. M4L
removed those fields but remained a diagnostic build, not a compatibility fix.

Pinned upstream 7543afd lacks the native save contracts now present in upstream
95130c3a8f8f746ea6412644571af4ee5de32366. The diff is 5 commits, 10 files,
148 additions and 21 removals. Upstream owns saveDate/elapsedTime/levelNum/saveFlags
on SaveGameNode, supplies the exact save virtual signatures, and accepts the
third DoSave argument. This is substantially stronger evidence than inventing
members on retail UI classes. Apparent local `info` and `totaltime` errors may be
cascades, but that remains unproved.

## Bounded implementation

Use the exact refreshed source pin with the existing M0-M4E iOS platform and
compiler-diagnostic patches. Do not apply M4F-M4L guessed compatibility/adapters.
Keep all three native save entry points no-write for this title-menu experiment.
Preserve the app identifier and Documents container; version is 0.9.0 build20.
The old diagnostic workflows are historical and incompatible with this refreshed
pin. Use only the new M4M workflow on this candidate branch, not those old lanes.
The candidate branch avoids their agent/** push filters. M4M is manual-only;
publishing this branch does not request an Apple build. No pull request is
opened yet because old PR filters also launch redundant full builds.

## Alternative hypothesis and discriminating observation

Retail scripts could still require additional unreleased API changes, or a
separate iOS compiler defect. A device `actor_zscript_compile_passed` followed by
`engine_first_frame_presented` supports the upstream mismatch explanation.
Remaining fatal ZScript errors in `zscript-compile.log` instead identify an
unresolved contract; do not suppress them or invent fields. The existing M4E
compiler diagnostics remain enabled. Save attempts emit
`SELACO_IOS_M4M_SAVE_BLOCKED write_attempted=0` and immediately return.

## Verification and limits

- Exact upstream checked out; complete M0-M4E chain plus guard materialized.
- Source-level regression checks pass; Python syntax, shell and generated-driver
  syntax checked locally. These are not a full C++ compile.
- Codebase Memory tools absent; project launcher exits127 (binary unavailable).
  Inspection used the narrow upstream diff and evidence-named source paths.
- Linux cannot build iPhoneOS; full compile/link/package awaits macOS runner.
- No proprietary archive inspected/copied, no signing material, no device changes.
- No title/menu, controls, gameplay, save/load or performance claim yet.

Install only as an update, never uninstall the old app first. First device test
is launch-to-title only; preserve runtime-bootstrap.txt and zscript-compile.log.

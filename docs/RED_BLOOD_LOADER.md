# Exact red-blood mod selection (local candidate)

The user's privately supplied `Mods/Brutal Selaco.pk3` identifies itself as
"Brutal Selaco (Red Blood mod)" by Nexxtic. Its archive digest was verified after
Wi-Fi transfer: c8889ddb25ea89601f19275c02b89fe4d3004220e40fdb1779a1e5a404427cac.
No archive bytes or mod source are included in this repository.

The launcher selects that exact regular/readable file only when its digest and
ZIP signature match, then passes one explicit `-file` argument pair. Absent,
directory or mismatching candidates leave base startup unchanged. It does not
scan the Mods folder. `-noautoload` and `-noautoexec` remain enabled. A future mod
update requires deliberate re-verification of the selected digest.

Markers `red_blood_mod_selected` / `red_blood_mod_not_selected` distinguish
selection, but do not claim the mod successfully compiled or displayed red blood.
Existing `actor_zscript_compile_passed` and a later device test are still required.
Save writes remain blocked by the M4M guard.

Complete patched public engine materializes locally; six generated-source
contract tests pass via `tests/test_red_blood_loader.py ENGINE_ROOT`. They are
source checks, not Apple compilation or device runtime proof.

The user approved the compact touch/gyro design before the integrated build.
The first controls compile is not a final delivery; gyro orientation was corrected
against the New Vegas reference during review and must be in the delivered build.

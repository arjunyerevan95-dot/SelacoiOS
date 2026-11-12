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

Build is on hold pending user review of touch/gyro layout designs. No second
Mac build has been launched. Do not publish modified workflow merely to test this
loader: publication would trigger an expensive build on the candidate branch.

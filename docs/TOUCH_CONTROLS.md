# Approved compact New Vegas-inspired Selaco touch layout

Build22 integrates the approved upper/mid-right cluster: Jump, Alt, Reload, Dash,
Wheel, Use and large adjacent Gyro/Fire. Lower-right and central space remain
available for relative swipe aiming. Left-side movement floats from touch origin,
hides on release and returns to neutral. Dragging Fire continues aiming while held;
starting in open space never captures Fire.

Gyro toggles independently from Alt. It defaults off, is suspended in menus and
uses elapsed sample time plus orientation mapping. Wheel tap selects previous
weapon; hold opens Weapons/Kick/Grenade/Crouch/Light/Settings. Slide/release selects;
center/outside cancels. Weapons opens numbered slots 1–8. The game continues while
local radials are open. Settings provides swipe/gyro sensitivity, still-phone
calibration, pause, and saved per-control position/size/opacity. Edit a position by
dragging; the last dragged control is selected for size/opacity adjustments.
Menu capture switches to six clear navigation/OK/Back controls.

UIKit/CoreMotion never call engine event APIs. A mutex-protected bounded state
bridge is drained on the engine thread in I_StartTic. Fractional look is retained;
non-finite samples rejected; movement clamped; menu transitions/cancellation and
backgrounding clear state. Presses released between tics are latched as pulses.

## Verification

Portable bridge tests compile production i_touch_input.cpp with interface-only
stubs, exercising axes, down/up, rapid taps, fractional motion, non-finite input,
menu transitions, GUI confirm, reset and concurrent producers. These do not prove
UIKit behavior or replace the Apple build. Public source patch chain materializes
from exact pin. Six red-blood source-contract checks pass. Physical touch comfort,
orientation/gyro response, menu coverage and game-specific actions still need
first device validation; no performance or full gameplay claim is made.

Save writes remain intentionally blocked. The existing build also retains its
silent probe audio configuration. Red-blood loading is an exact digest allowlist;
no other mods or private game assets are included in the IPA/repository.

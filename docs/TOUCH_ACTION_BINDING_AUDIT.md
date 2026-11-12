# Selaco touch action registry audit

Source: GZSelaco `95130c3a8f8f746ea6412644571af4ee5de32366`, build23
materialized tree, `wadsrc/static/engine/commonbinds.txt`, `defbinds.txt`, and
`src/common/console/keydef.h`. Every non-navigation command below was checked
against those actual default bindings. These are native defaults, not a claim
that the user's current in-game rebindings still match them.

`i_touch_actions.h` is a portable catalog only. It does not dispatch input or
change controls. Persist stable string IDs, not array indexes. `FindTouchAction`
returns null for unknown IDs; callers should preserve or explicitly reset
unknown saved assignments rather than silently invoking another action.

Hold means paired press/release while contact is held. Pulse means one complete
press/release. A radial may pulse a Hold action for a brief activation, but must
not leave it down; persistent latching belongs to separately tested UI state.
Alternate fire is the game's `+altattack`: ADS is weapon-dependent. The registry
does not change that native behavior. `switch_gadget` is a Hold action because
the native command is `+switchGadget`, not an invented one-shot command.

Gameplay and Automap entries can share a key with different meanings. Present
map actions only in map context, and route Navigation through the GUI adapter.
Map/Codex opening keys alone do not provide close/navigation while GUI capture
is active. `pause` uses the actual controller Start binding (`menu_main`);
Navigation `menu_back` uses Escape, rather than claiming Escape has a keyboard
`menu_main` binding. `native_wheel` is Alt, distinct from previous-weapon wheel-up.

Excluded intentionally: save, load, quicksave, quickload and quit. Saving remains
restricted in the candidate and must not become available through remapping.
Native screenshot/options/console are cataloged but need not be default buttons.
Local overlay actions (gyro toggle, customization, radial/submenu navigation) are
not native key commands and should use separate local dispatch, not fake keys.

| Stable ID | Label | Scan code | Mode | Native command | Context |
|---|---|---|---|---|---|
| `fire` | Fire | `0x100` | Hold | `+attack` | Gameplay |
| `alt` | Alternate fire / ADS | `0x101` | Hold | `+altattack` | Gameplay |
| `jump` | Jump | `0x39` | Hold | `+jump` | Gameplay |
| `dash` | Dash | `0x2a` | Hold | `+DashMode` | Gameplay |
| `use` | Use | `0x12` | Hold | `+use` | Gameplay |
| `reload` | Reload | `0x13` | Hold | `+reload` | Gameplay |
| `use_reload` | Use / Reload | `0x1c2` | Hold | `+usereload` | Gameplay |
| `crouch` | Toggle crouch | `0x2e` | Pulse | `crouch` | Gameplay |
| `crouch_hold` | Hold crouch | `0x1d` | Hold | `+crouch` | Gameplay |
| `melee` | Melee | `0x10` | Pulse | `meleeButton` | Gameplay |
| `gadget` | Use gadget | `0x22` | Pulse | `useGadget` | Gameplay |
| `switch_gadget` | Switch gadget | `0x23` | Hold | `+switchGadget` | Gameplay |
| `meds` | Use meds | `0x2c` | Pulse | `useMeds` | Gameplay |
| `ability` | Use ability | `0x102` | Pulse | `useability` | Gameplay |
| `ability_previous` | Previous ability | `0x1a` | Pulse | `previousAbility` | Gameplay |
| `ability_next` | Next ability | `0x1b` | Pulse | `nextAbility` | Gameplay |
| `native_wheel` | Game weapon wheel | `0x38` | Pulse | `weaponWheel` | Gameplay |
| `weapon_last` | Last weapon | `0x14` | Pulse | `LastWeapon` | Gameplay |
| `weapon_previous` | Previous weapon | `0x198` | Pulse | `weapprev` | Gameplay |
| `weapon_next` | Next weapon | `0x199` | Pulse | `weapnext` | Gameplay |
| `weapon_1` | Weapon 1 | `0x02` | Pulse | `slot 1` | Gameplay |
| `weapon_2` | Weapon 2 | `0x03` | Pulse | `slot 2` | Gameplay |
| `weapon_3` | Weapon 3 | `0x04` | Pulse | `slot 3` | Gameplay |
| `weapon_4` | Weapon 4 | `0x05` | Pulse | `slot 4` | Gameplay |
| `weapon_5` | Weapon 5 | `0x06` | Pulse | `slot 5` | Gameplay |
| `weapon_6` | Weapon 6 | `0x07` | Pulse | `slot 6` | Gameplay |
| `weapon_7` | Weapon 7 | `0x08` | Pulse | `slot 7` | Gameplay |
| `weapon_8` | Weapon 8 | `0x09` | Pulse | `slot 8` | Gameplay |
| `weapon_9` | Weapon 9 | `0x0a` | Pulse | `slot 9` | Gameplay |
| `weapon_0` | Weapon 0 | `0x0b` | Pulse | `slot 0` | Gameplay |
| `light` | Flashlight | `0x21` | Pulse | `Toggle_Flashlight` | Gameplay |
| `map` | Map | `0x0f` | Pulse | `togglemap` | Gameplay |
| `codex` | Codex | `0x3a` | Pulse | `codex` | Gameplay |
| `objectives` | Objectives | `0x32` | Pulse | `printObjectives` | Gameplay |
| `pause` | Pause / Menu | `0x1b8` | Pulse | `menu_main` | Gameplay |
| `options` | Game options | `0x3e` | Pulse | `openmenu SelacoOptionMenu` | Gameplay |
| `console` | Console | `0x29` | Pulse | `toggleconsole` | Gameplay |
| `screenshot` | Screenshot | `0xb7` | Pulse | `screenshot` | Gameplay |
| `forward` | Move forward | `0x11` | Hold | `+forward` | Gameplay |
| `back` | Move backward | `0x1f` | Hold | `+back` | Gameplay |
| `left` | Strafe left | `0x1e` | Hold | `+moveleft` | Gameplay |
| `right` | Strafe right | `0x20` | Hold | `+moveright` | Gameplay |
| `move_up` | Move up | `0xc9` | Hold | `+moveup` | Gameplay |
| `move_down` | Move down | `0xd2` | Hold | `+movedown` | Gameplay |
| `land` | Land | `0xc7` | Pulse | `land` | Gameplay |
| `look_up` | Look up | `0xd1` | Hold | `+lookup` | Gameplay |
| `look_down` | Look down | `0xd3` | Hold | `+lookdown` | Gameplay |
| `center_view` | Center view | `0xcf` | Pulse | `centerview` | Gameplay |
| `map_texture` | Map textures | `0x19` | Pulse | `am_toggletexture` | Automap |
| `map_clear_marks` | Clear map marks | `0x2e` | Pulse | `am_clearmarks` | Automap |
| `map_overview` | Map overview | `0x18` | Pulse | `am_gobig` | Automap |
| `map_legend` | Map legend | `0x26` | Pulse | `am_togglelegend` | Automap |
| `map_follow` | Map follow | `0x21` | Pulse | `am_togglefollow` | Automap |
| `map_pan_right` | Map pan right | `0xcd` | Hold | `+am_panright` | Automap |
| `map_pan_left` | Map pan left | `0xcb` | Hold | `+am_panleft` | Automap |
| `map_pan_up` | Map pan up | `0xc8` | Hold | `+am_panup` | Automap |
| `map_pan_down` | Map pan down | `0xd0` | Hold | `+am_pandown` | Automap |
| `map_zoom_in` | Map zoom in | `0xd1` | Hold | `+am_zoomin` | Automap |
| `map_zoom_out` | Map zoom out | `0xc9` | Hold | `+am_zoomout` | Automap |
| `menu_up` | Up | `0xc8` | Pulse | `` | Navigation |
| `menu_down` | Down | `0xd0` | Pulse | `` | Navigation |
| `menu_left` | Left | `0xcb` | Pulse | `` | Navigation |
| `menu_right` | Right | `0xcd` | Pulse | `` | Navigation |
| `confirm` | Confirm | `0x1c` | Pulse | `` | Navigation |
| `menu_back` | Back / Close | `0x01` | Pulse | `` | Navigation |

## Validation

`c++ -std=c++11 -Wall -Wextra -Werror -pedantic -Ioverlays/gzselaco-ios tests/touch_actions_test.cpp -o /tmp/selaco-touch-actions-test && /tmp/selaco-touch-actions-test`

Tests cover unique/nonempty IDs, valid scan-code range, lookup identity and
unknown input, all ten weapon slots, key requested mappings, hold/pulse modes,
contexts and exclusion of save/load actions. A local audit also checked every
nonempty command against the two pinned binding files. No iOS build or device
validation is implied; no UI, input bridge or workflow changed for this catalog.

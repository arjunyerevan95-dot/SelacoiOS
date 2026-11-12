#pragma once
#include <cstddef>
#include <cstring>

namespace SelacoIOS {
// Persist string IDs, never catalog indexes. Additions may reorder this catalog.
// Keys follow the native default bindings, not a direct console-command executor.
// Rebinding those keys in the game changes their effective behavior.
enum class TouchActionMode { Hold, Pulse };
enum class TouchActionContext { Gameplay, Automap, Navigation };
struct TouchAction {
    const char *id;
    const char *label;
    int scanCode;
    TouchActionMode mode;
    const char *defaultCommand;
    TouchActionContext context;
};
inline const TouchAction *TouchActionCatalog(std::size_t &count) {
    using M = TouchActionMode;
    using C = TouchActionContext;
    static const TouchAction actions[] = {
        {"fire", "Fire", 0x100, M::Hold, "+attack", C::Gameplay},
        {"alt", "Alternate fire / ADS", 0x101, M::Hold, "+altattack", C::Gameplay},
        {"jump", "Jump", 0x39, M::Hold, "+jump", C::Gameplay},
        {"dash", "Dash", 0x2a, M::Hold, "+DashMode", C::Gameplay},
        {"use", "Use", 0x12, M::Hold, "+use", C::Gameplay},
        {"reload", "Reload", 0x13, M::Hold, "+reload", C::Gameplay},
        {"use_reload", "Use / Reload", 0x1c2, M::Hold, "+usereload", C::Gameplay},
        {"crouch", "Toggle crouch", 0x2e, M::Pulse, "crouch", C::Gameplay},
        {"crouch_hold", "Hold crouch", 0x1d, M::Hold, "+crouch", C::Gameplay},
        {"melee", "Melee", 0x10, M::Pulse, "meleeButton", C::Gameplay},
        {"gadget", "Use gadget", 0x22, M::Pulse, "useGadget", C::Gameplay},
        {"switch_gadget", "Switch gadget", 0x23, M::Hold, "+switchGadget", C::Gameplay},
        {"meds", "Use meds", 0x2c, M::Pulse, "useMeds", C::Gameplay},
        {"ability", "Use ability", 0x102, M::Pulse, "useability", C::Gameplay},
        {"ability_previous", "Previous ability", 0x1a, M::Pulse, "previousAbility", C::Gameplay},
        {"ability_next", "Next ability", 0x1b, M::Pulse, "nextAbility", C::Gameplay},
        {"native_wheel", "Game weapon wheel", 0x38, M::Pulse, "weaponWheel", C::Gameplay},
        {"weapon_last", "Last weapon", 0x14, M::Pulse, "LastWeapon", C::Gameplay},
        {"weapon_previous", "Previous weapon", 0x198, M::Pulse, "weapprev", C::Gameplay},
        {"weapon_next", "Next weapon", 0x199, M::Pulse, "weapnext", C::Gameplay},
        {"weapon_1", "Weapon 1", 0x02, M::Pulse, "slot 1", C::Gameplay},
        {"weapon_2", "Weapon 2", 0x03, M::Pulse, "slot 2", C::Gameplay},
        {"weapon_3", "Weapon 3", 0x04, M::Pulse, "slot 3", C::Gameplay},
        {"weapon_4", "Weapon 4", 0x05, M::Pulse, "slot 4", C::Gameplay},
        {"weapon_5", "Weapon 5", 0x06, M::Pulse, "slot 5", C::Gameplay},
        {"weapon_6", "Weapon 6", 0x07, M::Pulse, "slot 6", C::Gameplay},
        {"weapon_7", "Weapon 7", 0x08, M::Pulse, "slot 7", C::Gameplay},
        {"weapon_8", "Weapon 8", 0x09, M::Pulse, "slot 8", C::Gameplay},
        {"weapon_9", "Weapon 9", 0x0a, M::Pulse, "slot 9", C::Gameplay},
        {"weapon_0", "Weapon 0", 0x0b, M::Pulse, "slot 0", C::Gameplay},
        {"light", "Flashlight", 0x21, M::Pulse, "Toggle_Flashlight", C::Gameplay},
        {"map", "Map", 0x0f, M::Pulse, "togglemap", C::Gameplay},
        {"codex", "Codex", 0x3a, M::Pulse, "codex", C::Gameplay},
        {"objectives", "Objectives", 0x32, M::Pulse, "printObjectives", C::Gameplay},
        {"pause", "Pause / Menu", 0x1b8, M::Pulse, "menu_main", C::Gameplay},
        {"options", "Game options", 0x3e, M::Pulse, "openmenu SelacoOptionMenu", C::Gameplay},
        {"console", "Console", 0x29, M::Pulse, "toggleconsole", C::Gameplay},
        {"screenshot", "Screenshot", 0xb7, M::Pulse, "screenshot", C::Gameplay},
        {"forward", "Move forward", 0x11, M::Hold, "+forward", C::Gameplay},
        {"back", "Move backward", 0x1f, M::Hold, "+back", C::Gameplay},
        {"left", "Strafe left", 0x1e, M::Hold, "+moveleft", C::Gameplay},
        {"right", "Strafe right", 0x20, M::Hold, "+moveright", C::Gameplay},
        {"move_up", "Move up", 0xc9, M::Hold, "+moveup", C::Gameplay},
        {"move_down", "Move down", 0xd2, M::Hold, "+movedown", C::Gameplay},
        {"land", "Land", 0xc7, M::Pulse, "land", C::Gameplay},
        {"look_up", "Look up", 0xd1, M::Hold, "+lookup", C::Gameplay},
        {"look_down", "Look down", 0xd3, M::Hold, "+lookdown", C::Gameplay},
        {"center_view", "Center view", 0xcf, M::Pulse, "centerview", C::Gameplay},
        {"map_texture", "Map textures", 0x19, M::Pulse, "am_toggletexture", C::Automap},
        {"map_clear_marks", "Clear map marks", 0x2e, M::Pulse, "am_clearmarks", C::Automap},
        {"map_overview", "Map overview", 0x18, M::Pulse, "am_gobig", C::Automap},
        {"map_legend", "Map legend", 0x26, M::Pulse, "am_togglelegend", C::Automap},
        {"map_follow", "Map follow", 0x21, M::Pulse, "am_togglefollow", C::Automap},
        {"map_pan_right", "Map pan right", 0xcd, M::Hold, "+am_panright", C::Automap},
        {"map_pan_left", "Map pan left", 0xcb, M::Hold, "+am_panleft", C::Automap},
        {"map_pan_up", "Map pan up", 0xc8, M::Hold, "+am_panup", C::Automap},
        {"map_pan_down", "Map pan down", 0xd0, M::Hold, "+am_pandown", C::Automap},
        {"map_zoom_in", "Map zoom in", 0xd1, M::Hold, "+am_zoomin", C::Automap},
        {"map_zoom_out", "Map zoom out", 0xc9, M::Hold, "+am_zoomout", C::Automap},
        {"menu_up", "Up", 0xc8, M::Pulse, "", C::Navigation},
        {"menu_down", "Down", 0xd0, M::Pulse, "", C::Navigation},
        {"menu_left", "Left", 0xcb, M::Pulse, "", C::Navigation},
        {"menu_right", "Right", 0xcd, M::Pulse, "", C::Navigation},
        {"confirm", "Confirm", 0x1c, M::Pulse, "", C::Navigation},
        {"menu_back", "Back / Close", 0x01, M::Pulse, "", C::Navigation},
    };
    count = sizeof(actions) / sizeof(actions[0]);
    return actions;
}
inline const TouchAction *FindTouchAction(const char *id) {
    if (!id || !*id) return nullptr;
    std::size_t count = 0;
    const TouchAction *actions = TouchActionCatalog(count);
    for (std::size_t i = 0; i < count; ++i)
        if (std::strcmp(actions[i].id, id) == 0) return actions + i;
    return nullptr;
}
} // namespace SelacoIOS

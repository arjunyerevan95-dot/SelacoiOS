#include "i_touch_actions.h"
#include <cassert>
#include <set>
#include <string>
int main() {
    using namespace SelacoIOS;
    std::size_t count = 0;
    const auto *all = TouchActionCatalog(count);
    assert(count >= 60);
    std::set<std::string> ids;
    for (std::size_t i = 0; i < count; ++i) {
        const auto &a = all[i];
        assert(a.id && *a.id && a.label && *a.label && a.defaultCommand);
        assert(a.scanCode > 0 && a.scanCode < 512);
        assert(ids.insert(a.id).second);
        assert(FindTouchAction(a.id) == &a);
        if (a.defaultCommand[0] == '+') assert(a.mode == TouchActionMode::Hold);
        assert(std::string(a.defaultCommand).find("save") == std::string::npos);
        assert(std::string(a.defaultCommand).find("load") == std::string::npos ||
               a.id == std::string("reload") || a.id == std::string("use_reload"));
    }
    assert(!FindTouchAction(nullptr) && !FindTouchAction("") && !FindTouchAction("unknown"));
    assert(!FindTouchAction("Map")); // persisted IDs are case-sensitive
    for (int i = 0; i <= 9; ++i) {
        const auto *a = FindTouchAction(("weapon_" + std::to_string(i)).c_str());
        assert(a && a->scanCode == (i ? i + 1 : 0x0b));
        assert(std::string(a->defaultCommand) == "slot " + std::to_string(i));
    }
    assert(FindTouchAction("map")->scanCode == 0x0f);
    assert(FindTouchAction("codex")->scanCode == 0x3a);
    assert(FindTouchAction("objectives")->scanCode == 0x32);
    assert(FindTouchAction("pause")->scanCode == 0x1b8);
    assert(FindTouchAction("native_wheel")->scanCode == 0x38);
    assert(FindTouchAction("weapon_previous")->scanCode == 0x198);
    assert(FindTouchAction("weapon_next")->scanCode == 0x199);
    assert(FindTouchAction("crouch")->mode == TouchActionMode::Pulse);
    assert(FindTouchAction("crouch_hold")->mode == TouchActionMode::Hold);
    assert(FindTouchAction("switch_gadget")->mode == TouchActionMode::Hold);
    assert(FindTouchAction("alt")->mode == TouchActionMode::Hold);
    assert(FindTouchAction("map_pan_up")->context == TouchActionContext::Automap);
    assert(FindTouchAction("menu_back")->context == TouchActionContext::Navigation);
    assert(!FindTouchAction("save") && !FindTouchAction("load") && !FindTouchAction("quicksave"));
}

#pragma once
#include "TitleActivation.hpp"
#include "MenuCursor.hpp"
namespace th143 {
struct TitleSceneEntryBindings {
    TitleActivationBindings& title;
    std::array<u32,4>& equipment;std::array<u32,4>& saved_equipment;
    u32& alternate;u32& reset_selection;RootFactoryHost& worker;
};
//4624e0 substate0 and the outer45f6e0 timer, before preview work is run.
// The background preview worker is launched through the caller's service.
bool enter_title_scene_page(TitleSceneEntryBindings&,u32& result);
}

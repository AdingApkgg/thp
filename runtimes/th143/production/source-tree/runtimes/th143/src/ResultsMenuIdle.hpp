#pragma once
#include "FailureMenu.hpp"
namespace th143 {
struct ResultsMenuIdleInput:FailureMenuGlobals {u32 day=0,within_day=0,day_scene_count=0,message_owner=0;};
//447db0 ->44aae0 substates0/1. Confirm/replay/unlock-message owners are separate.
i32 results_menu_idle_frame(PauseMenu&,SaveData&,GameOverGlobals&,ResultsMenuIdleInput&,AnmWorld&,AnmOverlay&,AnmView hud,FailureMenuHost&);
}

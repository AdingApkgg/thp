#pragma once
#include "ResultsMenuIdle.hpp"
namespace th143 {
struct ResultsMenuExitHost:FailureMenuHost {virtual bool results_exit_fade()=0;};
// Results substates0/1/2 for choices0/1/3, with game-state next-scene writes.
i32 results_menu_exit_frame(PauseMenu&,SaveData&,GameOverGlobals&,ResultsMenuIdleInput&,AnmWorld&,AnmOverlay&,AnmView hud,ResultsMenuExitHost&,AnmView game,u32& scene,const std::array<u32,10>& day_first);
}

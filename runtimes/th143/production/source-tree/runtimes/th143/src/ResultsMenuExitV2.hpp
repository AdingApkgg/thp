#pragma once
#include "ResultsMenuExit.hpp"
#include "PauseReplayPage.hpp"
namespace th143 {
// Original44aae0 results choices0/1/2/3 and replay list/name substates7/8.
i32 results_menu_exit_frame_v2(PauseMenu&,SaveData&,GameOverGlobals&,ResultsMenuIdleInput&,AnmWorld&,AnmOverlay&,AnmView,ResultsMenuExitHost&,AnmView,u32&,const std::array<u32,10>&,PauseReplayPageHost&);
}

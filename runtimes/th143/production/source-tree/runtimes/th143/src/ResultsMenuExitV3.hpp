#pragma once
#include "ResultsMenuExit.hpp"
#include "PauseReplayPage.hpp"
#include "ResultsEquipmentPage.hpp"
namespace th143 {
// Original44aae0 results choices0/1/2/3/4, replay list/name7/8 and equipment10.
i32 results_menu_exit_frame_v3(PauseMenu&,SaveData&,GameOverGlobals&,ResultsMenuIdleInput&,AnmWorld&,AnmOverlay&,AnmView,ResultsMenuExitHost&,AnmView,u32&,const std::array<u32,10>&,PauseReplayPageHost&,PauseEquipmentPageHost&);
}

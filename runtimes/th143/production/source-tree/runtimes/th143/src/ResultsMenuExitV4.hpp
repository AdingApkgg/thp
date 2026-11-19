#pragma once
#include "ResultsMenuExit.hpp"
#include "PauseReplayPage.hpp"
#include "ResultsEquipmentPage.hpp"
#include "ResultsManualPage.hpp"
namespace th143 {
// Original44aae0 results all six choices, replay7/8, equipment10 and Manual11.
i32 results_menu_exit_frame_v4(PauseMenu&,SaveData&,GameOverGlobals&,ResultsMenuIdleInput&,AnmWorld&,AnmOverlay&,AnmView,ResultsMenuExitHost&,AnmView,u32&,const std::array<u32,10>&,PauseReplayPageHost&,PauseEquipmentPageHost&,PauseManualPageHost&);
}

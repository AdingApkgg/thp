#pragma once
#include "GameOver.hpp"
namespace th143 {
//44a7a0 opening only; results navigation has its own callback paths.
bool open_results_menu(PauseMenu&,SaveData&,GameOverGlobals&,AnmWorld&,AnmOverlay&,u32 primary,u32 scene,u32 equipment_used,GameOverHost&);
}

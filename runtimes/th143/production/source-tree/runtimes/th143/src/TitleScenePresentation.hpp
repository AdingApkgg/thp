#pragma once
#include "TitleSceneEntry.hpp"
namespace th143 {
//463a00: day unlock restrictions, disabled cursor entries and clear sprites.
bool refresh_title_scene_choices(GameTitleRuntime&,AnmResourceWorld&,SaveData&);
//4640e0: current selection, screenshot request, equipment and clear indicators.
bool refresh_title_scene_selection(GameTitleRuntime&,GameCheatRuntime&,AnmResourceWorld&,SaveData&);
}

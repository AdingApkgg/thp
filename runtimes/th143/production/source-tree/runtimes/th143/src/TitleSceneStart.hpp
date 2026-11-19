#pragma once
#include "GameTitleRuntime.hpp"
#include "TitleMainIntro.hpp"
#include "SaveFileWriter.hpp"
#include "MusicCommandQueue.hpp"
#include "TitleScenePage.hpp"
namespace th143 {
struct TitleSceneStartBindings {
    GameTitleRuntime& title;SaveData& save;AnmResourceWorld& world;
    AnmView application,audio,game_state;
    std::array<u32,4>& equipment;std::array<u32,4>& saved_equipment;
    u32& scene_descriptor;u32& menu_selection;
    RootFactoryHost& worker;SaveFileServices& files;GameSavedFile* loaded=nullptr;TitleScenePageBindings* responses=nullptr;
};
//4624e0 confirm4's clock38 handoff. Saved responses must have been consumed:
// the original45f580 loop does not pop a nonempty saved-object queue.
bool start_selected_title_scene(TitleSceneStartBindings&,u32& result);
}

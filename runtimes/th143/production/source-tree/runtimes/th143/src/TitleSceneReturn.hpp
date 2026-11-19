#pragma once
#include "TitleScenePage.hpp"
#include "SaveFileWriter.hpp"
namespace th143 {
//4624e0 equipment-return3 and delayed return-to-main6, with the shared
// preview response tail and45f6e0 clock. Confirm/start4 is separate.
bool advance_title_scene_return(TitleScenePageBindings&,SaveFileServices&,GameSavedFile*,u32& result);
}

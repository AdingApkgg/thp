#pragma once
#include "TitleSceneEntry.hpp"
#include "AnmMenuWorld.hpp"
namespace th143 {
//45f6e0 music prefix,also required while the returned scene page opens.
bool advance_title_return_music(TitleActivationBindings&);
//45f6e0 state0/return-mode6,including direct4624e0 entry with music pending.
bool activate_returned_title_scene(TitleSceneEntryBindings&,AnmMenuWorld&,u32& result);
// The returned page's first negative-time frames have no page-body actions.
bool tick_title_return_wait(TitleActivationBindings&,u32& result);
}

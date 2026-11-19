#pragma once
#include "GameTitleRuntime.hpp"
#include "AnmResourceWorld.hpp"
namespace th143 {
//45fb70 main-page substates0/1 and45f6e0's timer tail. The caller has
// selected title state1; music/fresh-title activation and substate2 input are
// separate bodies. Completes the current frame when it enters substate2.
bool select_title_state(GameTitleRuntime&,i32 state);
bool advance_title_main_intro(GameTitleRuntime&,AnmResourceWorld&,u32& result);
}

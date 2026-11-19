#pragma once
#include "TitleOptionControl.hpp"
namespace th143 {
//45f6e0 state0/return-mode2, with no trophy or pending39. Startup music
// prefix is supplied by the caller;4650c0 is a separately gated child body.
bool activate_returned_title_replay(AnmView title,u32 self,TitleOptionControlHost&,u32& result);
}

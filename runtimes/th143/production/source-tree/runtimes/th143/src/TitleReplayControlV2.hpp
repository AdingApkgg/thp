#pragma once
#include "TitleOptionControl.hpp"
namespace th143 {
// Full4650c0 through45f6e0 including its outer clock. Native single-thread
// resource critical-section flag0 and clear startup-music flag are required.
bool advance_title_replay_control_v2(AnmView title,u32 self,TitleOptionControlHost&,u32& result,bool outer_clock=true);
}

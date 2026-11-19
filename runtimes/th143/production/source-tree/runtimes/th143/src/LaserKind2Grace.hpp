#pragma once
#include "AnmState.hpp"
namespace th143 {
bool activate_laser_kind2_grace(AnmView,u32 rate=0x4e40b0);
bool update_laser_kind2_grace(AnmView,AnmTimerHost&,i32& result);
}

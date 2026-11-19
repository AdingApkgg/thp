#pragma once
#include "AnmState.hpp"
namespace th143 {
//4316d0: award normal-clear score and reset the HUD bonus clock.
void award_hud_clear_bonus(AnmView,u32& score,u32 rate_token=0x4e40b0);
}

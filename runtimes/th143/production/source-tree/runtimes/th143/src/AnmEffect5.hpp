#pragma once
#include "AnmVm.hpp"

namespace th143 {
void anm_effect5_initialize(AnmView,u8* data,u32 token,u32 rate,Rng&); //409dc0 /41af40
bool anm_effect5_step(u8* data,AnmTimerHost&,Rng&); //409ec0
}

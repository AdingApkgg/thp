#pragma once
#include "AnmInterpolation.hpp"

namespace th143 {
// 410520's 0xa8-byte interpolation: six floats plus a derived packed color.
// Endpoints return a value without overwriting the stored current vector.
bool stage_fog_interpolate(AnmView,AnmTimerHost&,std::array<u32,7>&);
void stage_fog_begin(AnmView,const std::array<u32,7>& start,const std::array<u32,7>& target,u32 duration,u32 mode,u32 rate);
}

#pragma once
#include "AnmState.hpp"
#include <array>
namespace th143 {
// Full418300, with copied current3c/target/global53b184 vectors. Source and
// target are outside the interpolation storage written before their reads.
void begin_anm_position_interpolation(AnmView,u32 duration,u32 mode,const std::array<u32,3>& from,const std::array<u32,3>& to,const std::array<u32,3>& zero);
}

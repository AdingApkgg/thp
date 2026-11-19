#pragma once
#include "AnmState.hpp"
namespace th143 {
// Original 43a978..43aa46/43ab11. Transform dispatch, bounds, ANM and
// collision belong to the caller and are deliberately separate operations.
bool advance_laser_kind0_linear(AnmView,float rate,bool& expired);
}

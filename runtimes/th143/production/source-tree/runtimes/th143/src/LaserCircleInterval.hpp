#pragma once
#include "AnmState.hpp"
#include <array>
namespace th143 {
// Original405c70: interval along a forward ray intersecting a circle.
// Positive finite radii only; rejected circles preserve the output words.
bool laser_circle_interval(const std::array<float,3>& origin,const std::array<float,3>& center,float angle,float radius,float& begin,float& end,bool& intersects);
}

#pragma once
#include "AnmState.hpp"
namespace th143 {
// Original404f60: rotated rectangle versus circle. Side-strip tangencies
// are inclusive; the four corner-distance comparisons are strict.
bool shot_rectangle_circle(float x,float y,float width,float height,float angle,float circle_x,float circle_y,float radius);
}

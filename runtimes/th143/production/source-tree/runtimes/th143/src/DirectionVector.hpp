#pragma once
#include "EclVm.hpp"

namespace th143 {
struct DirectionVector { float x = 0, y = 0; };
// Native 418440/408750 FSINCOS then multiply, storing only two float words.
// Finite gameplay interval +/-64*tau, including pre-wrap factory angles.
// Larger/non-finite inputs remain explicit unsupported cases.
bool direction_vector(float angle, float speed, DirectionVector&);
}

#pragma once
#include "AnmInterpolation.hpp"
namespace th143 {
// Original417e00, shared by enemy angle/speed and scalar animation slots.
// The0x30-byte layout preserves the internal current value at the endpoint.
bool scalar_interpolate(AnmView,AnmTimerHost&,float& result);
void scalar_reset_timer(AnmView,AnmTimerHost&);
}

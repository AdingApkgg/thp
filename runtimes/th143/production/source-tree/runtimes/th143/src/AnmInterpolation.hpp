#pragma once
#include "AnmState.hpp"
#include <array>

namespace th143 {
// 404460 arithmetic/sine easing, retaining the original float phase rounding.
bool anm_easing(i32 mode, float elapsed, float duration, float& result);
// 478b20 / 4790f0. Returned endpoint need not overwrite the stored current value.
bool anm_interpolate_integer(AnmView, AnmTimerHost&, u32& result);
bool anm_interpolate_vec2(AnmView, AnmTimerHost&, std::array<u32, 2>& result);
// Original409880 Float3 and478780 Int3 color specialization.
bool anm_interpolate_vec3(AnmView, AnmTimerHost&, bool integer, std::array<u32, 3>& result);
// 478480 position/rotation/primary and secondary color/alpha/three scales.
// Scalar rotation/UV interpolation slots remain explicit unsupported cases.
bool anm_interpolate(AnmView, AnmTimerHost&);
}

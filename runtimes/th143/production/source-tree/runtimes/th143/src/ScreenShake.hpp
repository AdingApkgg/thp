#pragma once
#include "AnmState.hpp"
#include "Rng.hpp"
#include <array>
namespace th143 {
struct ScreenShakeGlobals {u32 paused=0,scale=0;std::array<u32,4> offsets{};Rng random;};
static_assert(sizeof(ScreenShakeGlobals)==32);
//471650 updates a mode1 screen effect. Scheduler/factory ownership is separate.
i32 step_screen_shake(AnmView,ScreenShakeGlobals&,AnmTimerHost&);
}

#pragma once
#include "AnmState.hpp"
#include <functional>
namespace th143 {
struct LaserKind0BounceServices {
 std::function<bool(i32)> sound;
 std::function<bool(const u8*,u32)> spawn;
};
// Actual439970 type40 dispatch and43a060 boundary replacement.
// Other transform types are explicit unsupported inputs.
bool dispatch_laser_kind0_bounce(AnmView,LaserKind0BounceServices&);
bool advance_laser_kind0_bounce(AnmView,LaserKind0BounceServices&,i32& result);
}

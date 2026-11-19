#pragma once
#include "LaserKind2RectangleCancel.hpp"
namespace th143 {
// 442570: a visual for every third point, color*2+0xb5, then mode1.
// The kind argument is unused; the original creates no cancellation items.
bool cancel_laser_kind2_full(AnmView,i32 kind,bool items,LaserKind2RectangleCancelHost&,i32& result);
}

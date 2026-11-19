#pragma once
#include "LaserKind2RectangleCancel.hpp"
namespace th143 {
// 442230, class2 slot24: circle mask and in-place point-buffer clipping.
// Its original fixed stack mask supports at most256 points.
bool cancel_laser_kind2_circle(AnmView,const std::array<float,3>& position,float radius,i32 kind,bool items,LaserKind2RectangleCancelHost&,i32& result);
}

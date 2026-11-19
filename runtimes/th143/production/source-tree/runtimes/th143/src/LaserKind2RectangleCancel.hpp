#pragma once
#include "LaserKind0RectangleCancel.hpp"
#include "LaserKind2Points.hpp"
namespace th143 {
struct LaserKind2RectangleCancelHost:LaserKind0RectangleCancelHost,LaserKind2PointHost {
 virtual bool laser_rectangle_mask_allocate(u32 bytes,u32& token,u8*& storage)=0;
 virtual bool laser_rectangle_mask_release(u32 token)=0;
};
// 441840: point mask, head-age trim and surviving curved-laser splits.
// laser_rectangle_spawn creates kind2 and receives its source curve token.
bool cancel_laser_kind2_rectangle(AnmView,u32 token,const std::array<float,3>& position,const std::array<float,3>& size,float angle,i32 kind,bool items,LaserKind2RectangleCancelHost&,i32& result);
}

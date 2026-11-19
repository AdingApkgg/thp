#pragma once
#include "AnmState.hpp"
#include <array>
namespace th143 {
struct LaserKind0RectangleCancelHost {
 virtual bool laser_rectangle_item(const std::array<float,3>&,i32 kind)=0;
 virtual bool laser_rectangle_visual(i32 script,const std::array<float,3>&)=0;
 virtual bool laser_rectangle_spawn(const u8* parameters,u32 bytes)=0;
};
// Actual43afb0: finite geometry, up to256 sixteen-pixel segments.
bool cancel_laser_kind0_rectangle(AnmView,const std::array<float,3>& position,const std::array<float,3>& size,float angle,i32 kind,bool items,LaserKind0RectangleCancelHost&,i32& result);
}

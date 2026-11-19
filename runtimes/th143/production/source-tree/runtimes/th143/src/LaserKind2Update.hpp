#pragma once
#include "LaserKind2Points.hpp"
#include "LaserKind2PolarPath.hpp"
#include "LaserKind2Grace.hpp"
namespace th143 {
struct LaserKind2UpdateHost:AnmTimerHost,LaserKind2PointHost,LaserCurveNodeHost {
 virtual bool laser_kind2_update_contact(u32 token,bool forced)=0;
 virtual bool laser_kind2_update_animation(u32 token,AnmView)=0;
};
// 43f7c0 with empty/100/8 transform programs and optional high-bit delay.
// Other active transforms are explicit unsupported branches.
bool update_laser_kind2(AnmView,u32 token,LaserKind2UpdateHost&,i32& result);
}

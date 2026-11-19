#pragma once
#include "LaserPathSegment.hpp"
namespace th143 {
struct LaserKind2PointHost {
 virtual ~LaserKind2PointHost()=default;
 virtual bool laser_point_read(u32,void*,u32)=0;
 virtual bool laser_point_write(u32,const void*,u32)=0;
};
// Geometry worker43f92d..43fa48, separate from transforms/contact/ANM/timers.
bool refresh_laser_kind2_points(AnmView,u32 token,LaserKind2PointHost&);
}

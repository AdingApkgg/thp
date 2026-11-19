#pragma once
#include "LaserKind2Vertices.hpp"
namespace th143 {
struct LaserKind2DrawHost:LaserKind2PointHost {
 virtual bool laser_draw_external(u32 animation_token,AnmView,u32 vertices,u32 count)=0;
 virtual bool laser_draw_secondary(u32 animation_token,AnmView)=0;
};
bool draw_laser_kind2(AnmView,u32 token,const std::array<i32,2>& origin,LaserKind2DrawHost&);
}

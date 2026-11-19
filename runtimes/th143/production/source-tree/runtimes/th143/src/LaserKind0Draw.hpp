#pragma once
#include "AnmState.hpp"
namespace th143 {
struct LaserKind0DrawHost {virtual ~LaserKind0DrawHost()=default;virtual bool laser_draw_animation(u32 token,AnmView)=0;};
bool draw_laser_kind0(AnmView,u32 token,LaserKind0DrawHost&);
}

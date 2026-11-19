#pragma once
#include "BulletMotionDay1.hpp"
#include "ScalarInterpolation.hpp"
namespace th143 {
void start_bullet_scale_transform(BulletView,u32 row,u32 rate);
bool update_bullet_scale_transform(BulletView,AnmTimerHost&);
}

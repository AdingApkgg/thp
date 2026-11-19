#pragma once
#include "BulletMotion.hpp"
#include <functional>
namespace th143 {
void bind_bullet_transform_sound(BulletMotionHost&,std::function<bool(i32)>);
bool start_bullet_extended_transform(BulletView,u32 row,u32 type,BulletMotionHost&,u32 rate_token);
i32 bullet_polar_acceleration(BulletView,BulletMotionHost&);
i32 bullet_transform_wait(BulletView,BulletMotionHost&);
}

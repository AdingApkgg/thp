#pragma once
#include "BulletMotion.hpp"
namespace th143 {
void start_bullet_timed_freeze(BulletView,u32 row,u32 global_rate_token);
i32 update_bullet_timed_freeze(BulletView,BulletMotionHost&);
}

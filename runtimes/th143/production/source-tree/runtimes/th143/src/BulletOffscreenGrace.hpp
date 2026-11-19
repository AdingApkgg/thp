#pragma once
#include "BulletMotion.hpp"
namespace th143 {
void start_bullet_offscreen_grace(BulletView,u32 row,u32 global_rate_token);
//416c60 mode0 countdown. Nonzero modes need the separate directional geometry.
i32 update_bullet_offscreen_grace(BulletView,BulletMotionHost&);
}

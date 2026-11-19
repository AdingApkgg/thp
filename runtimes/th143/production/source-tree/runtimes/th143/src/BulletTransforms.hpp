#pragma once
#include "BulletMotion.hpp"

namespace th143 {
// 414630: activate/advance transform rows. Currently handles the first-scene
// appearance and fast-shot rows plus the per-bullet extra field (0x8000).
// Other types fail explicitly after the original active/parallel gates.
bool bullet_transform(BulletView, BulletMotionHost&, u32 global_rate_token);
// 415960: velocity during the first 17 fast-shot ticks; returns 1 on expiry.
i32 bullet_fast_velocity(BulletView, BulletMotionHost&);
}

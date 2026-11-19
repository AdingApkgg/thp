#pragma once
#include "BulletMotion.hpp"
#include "BulletPool.hpp"

namespace th143 {
struct BulletManagerHost {
    virtual ~BulletManagerHost() = default;
    virtual bool timer_rate(u32 token, float& rate) = 0;
    virtual bool update(BulletView, u32 bullet_token, i32& status) = 0;
    virtual bool forced_contact(BulletView, u32 bullet_token) = 0;
};
// 413550: prefetch the next active node before updating the current bullet;
// rebuild six draw lists, count survivors and advance their separate age timer.
// root_flags is the original game-root+80 word, or zero when the root is absent.
bool bullet_manager_step(BulletPool&, u32 root_flags, BulletManagerHost&);
}

#pragma once
#include "BulletMotion.hpp"
#include "PlayerCollision.hpp"
#include <array>

namespace th143 {
struct BulletContactHost : PlayerHitHost {
    virtual bool graze(PlayerState&, const std::array<float, 3>& position) = 0;
    virtual bool cancellation_visual(i32 script, const std::array<float, 3>& position,
                                      const std::array<float, 3>& target) = 0;
    virtual bool interrupt(BulletView b, u32 slot, i32 id) {
        const u32 vm = slot ? 0x5f4 : 0x28;
        if (b.get(vm + 0x5c4)) return false;
        b.put(vm + 0x4a0, u32(id)); return true;
    }
};
// Original 4131a0 consumes the player contact query and applies the bullet's
// hit/graze transitions. Actual player hit/graze and cancellation visuals are
// required host services; unavailable services return -2 rather than vanish.
i32 bullet_contact(BulletView, PlayerState&, float shot_hit_radius, bool hud_blocked,
                   bool forced, float elapsed, BulletContactHost&);
}

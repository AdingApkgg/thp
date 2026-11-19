#include "BulletContact.hpp"

namespace th143 {
i32 bullet_contact(BulletView b, PlayerState& player, float hit_radius, bool hud_blocked,
                   bool forced, float elapsed, BulletContactHost& host) {
    const u32 flags = b.get(0x20);
    if (!(flags & 2)) return 0;
    float width = b.floating(0xbe0), height = b.floating(0xbe4);
    if (flags & 0x40) { width *= b.floating(0x13bc); height *= b.floating(0x13bc); }
    const float x = b.floating(0xbc0), y = b.floating(0xbc4);
    const i32 result = flags & 0x10 ? player_circle_collision(player, hit_radius, hud_blocked, x, y, width, forced, host)
                                  : player_rectangle_collision(player, hud_blocked, x, y, width, height, forced, host);
    if (result == -2) return -2;
    if (result == 1) {
        if (!b.get(0x24)) {
            b.state(3);
            if (!host.interrupt(b, 0, 1)) return -2;
            if ((b.get(0x60c) & 1) && !host.interrupt(b, 1, 1)) return -2;
            const i32 script = signed_word(b.get(0xc00));
            if (script >= 0) {
                std::array<float, 3> position, target;
                for (u32 i = 0; i < 3; ++i) {
                    position[i] = b.floating(0xbc0 + i * 4);
                    target[i] = (b.floating(0xbcc + i * 4) * elapsed) * 10.f;
                }
                if (!host.cancellation_visual(script, position, target)) return -2;
            }
        }
    } else if (result == 2 && !(b.get(0x20) & 4)) {
        const std::array<float, 3> position{b.floating(0xbc0), b.floating(0xbc4), b.floating(0xbc8)};
        if (!host.graze(player, position)) return -2;
        b.put(0x20, b.get(0x20) | 4);
    }
    return result;
}
}

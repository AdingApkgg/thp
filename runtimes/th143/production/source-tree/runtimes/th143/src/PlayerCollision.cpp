#include "PlayerCollision.hpp"

namespace th143 {
namespace {
i32 hit_result(PlayerState& player, bool blocked, bool forced, PlayerHitHost& host) {
    if ((player.get(0x1847c) & 0x20) || blocked) return 0;
    if (forced) return 2;
    const u32 state = player.get(0x684);
    if (state == 2 || state == 4 || state == 3) return 0;
    if (signed_word(player.get(0x1846c)) <= 0 && !host.hit(player)) return -2;
    return 1;
}
}
i32 player_circle_collision(PlayerState& player, float hit_radius, bool blocked,
                            float x, float y, float radius, bool forced, PlayerHitHost& host) {
    const float dy = player.floating(0x5e4) - y, dx = player.floating(0x5e0) - x;
    const float distance = dx * dx + dy * dy;
    if (player.get(0x1847c) & 8) hit_radius = (player.floating(0x184b0) * real(0x40666666)) * hit_radius;
    const float radius_squared = radius * radius;
    const float threshold = hit_radius * hit_radius + radius_squared;
    // COMISS/JB also takes the hit path for unordered comparisons.
    if (!(distance >= threshold)) return hit_result(player, blocked, forced, host);
    float graze = radius / 2.5f;
    if (40.f > graze) graze = 40.f;
    graze += hit_radius;
    const float outer = graze * graze + radius_squared;
    return distance >= outer ? 0 : 2;
}
i32 player_rectangle_collision(PlayerState& player, bool blocked, float x, float y,
                               float width, float height, bool forced, PlayerHitHost& host) {
    const float half_width = width * .5f, half_height = height * .5f;
    const float min_x = player.floating(0x630), min_y = player.floating(0x634);
    const float max_x = player.floating(0x63c), max_y = player.floating(0x640);
    const bool outside = min_x > x + half_width || min_y > y + half_height ||
                         x - half_width > max_x || y - half_height > max_y;
    if (!outside) return hit_result(player, blocked, forced, host);
    if (min_x > x + 24.f || min_y > y + 24.f || x - 24.f > max_x || y - 24.f > max_y) return 0;
    return 2;
}
}

#include "PlayerEffects.hpp"

namespace th143 {
namespace {
void timer(PlayerState& p, u32 at, u32 count, u32 rate_token) {
    if (!(p.get(at + 16) & 1)) {
        p.put(at + 12, rate_token); p.put(at + 16, p.get(at + 16) | 1);
    }
    p.put(at, count - 1); p.put(at + 4, count); p.put(at + 8, word(float(signed_word(count))));
}
}
bool player_hit(PlayerState& player, PlayerEffectsHost& host, u32 rate_token) {
    if (!(player.get(0x1847c) & 4) && !host.sound(2, false, 0.f)) return false;
    const std::array<float, 3> position{player.floating(0x5e0), player.floating(0x5e4), player.floating(0x5e8)};
    if (!host.effect(20, position)) return false;
    timer(player, 0x68c, 0, rate_token); player.put(0x684, 4);
    timer(player, 0x18468, 6, rate_token);
    if (!host.bind_player(player, 0)) return false;
    player.put(0x14 + 0x594, 0);
    return host.update_player_visual(player);
}
bool player_graze(PlayerState& player, const std::array<float, 3>& position,
                  PlayerEffectGlobals& globals, PlayerEffectsHost& host) {
    if (signed_word(globals.graze) < 99999999) ++globals.graze;
    const float angle = globals.gameplay_rng.signed_unit() * real(0x40490fdb);
    ++globals.item_graze_counter;
    if (!host.item(13, position, angle, real(0x3fcccccd))) return false;
    const std::array<float, 3> midpoint{(player.floating(0x5e0) + position[0]) * .5f,
                                      (player.floating(0x5e4) + position[1]) * .5f, 0.f};
    if (!host.effect(14, midpoint)) return false;
    return host.sound(42, true, position[0]);
}
}

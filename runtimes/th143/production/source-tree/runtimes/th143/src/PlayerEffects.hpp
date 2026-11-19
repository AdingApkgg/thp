#pragma once
#include "PlayerState.hpp"
#include "Rng.hpp"

namespace th143 {
struct PlayerEffectGlobals {
    u32 graze = 0, item_graze_counter = 0;
    Rng gameplay_rng;
};
struct PlayerEffectsHost {
    virtual ~PlayerEffectsHost() = default;
    virtual bool sound(i32 id, bool spatial, float x) = 0;
    virtual bool effect(i32 script, const std::array<float, 3>& position) = 0;
    virtual bool item(i32 type, const std::array<float, 3>& position, float angle, float speed) = 0;
    virtual bool bind_player(PlayerState&, i32 script) = 0;
    virtual bool update_player_visual(PlayerState&) = 0;
};
// Original 44f140 and44f6f0. Services return false only when unavailable;
// an exhausted visual/item pool may complete a request without an object.
bool player_hit(PlayerState&, PlayerEffectsHost&, u32 rate_token);
bool player_graze(PlayerState&, const std::array<float, 3>& position,
                  PlayerEffectGlobals&, PlayerEffectsHost&);
}

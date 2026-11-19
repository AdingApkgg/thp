#pragma once
#include "PlayerState.hpp"

namespace th143 {
// Return 0=no contact, 1=hit, 2=graze/forced contact, -2=missing hit service.
// hud_blocked corresponds only to a non-null HUD with +198 nonzero.
i32 player_circle_collision(PlayerState&, float shot_hit_radius, bool hud_blocked,
                            float x, float y, float radius, bool forced, PlayerHitHost&);
i32 player_rectangle_collision(PlayerState&, bool hud_blocked, float x, float y,
                               float width, float height, bool forced, PlayerHitHost&);
}

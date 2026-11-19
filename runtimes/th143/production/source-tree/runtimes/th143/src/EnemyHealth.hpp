#pragma once
#include "ActorState.hpp"
namespace th143 {
struct EnemyPhaseGlobals {
    u32 special_flags=0,manager_phase=0;
    i32 countdown_seconds=0,countdown_hundredths=0;
};
// Original41d610. Damage arithmetic wraps before the signed division in the
// sevenfold-health mode; the accumulated damage changes in both modes.
void damage_enemy_health(ActorState&,i32 damage);
// Original428c90. Returns a script token, including zero, and preserves the
// original health-before-time priority and its cache/reset ordering.
u32 advance_enemy_phase(ActorState&,EnemyPhaseGlobals&,u32 rate_token=0x4e40b0);
}

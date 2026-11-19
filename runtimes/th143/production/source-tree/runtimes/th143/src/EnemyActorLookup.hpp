#pragma once
#include "EclVm.hpp"
namespace th143 {
struct EnemyActorIdentityEntry{u32 id,token;};
//41dc40 returns the last visited actor for a missing nonzero ID.
u32 enemy_actor_lookup(const EnemyActorIdentityEntry*,u32 count,u32 id);
}

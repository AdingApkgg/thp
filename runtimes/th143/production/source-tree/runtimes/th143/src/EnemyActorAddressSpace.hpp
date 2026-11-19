#pragma once
#include "AnmState.hpp"
namespace th143 {
class EnemyScripts;
// Logical OS allocation state outlives an EnemyManager. Actor IDs belong to
// that manager and may restart while the allocator continues independently.
struct EnemyActorAddressSpace {
    u32 next=0x50010000,allocations=0;
    bool allocate(u32& token);
};
void bind_enemy_actor_address_space(EnemyScripts&,EnemyActorAddressSpace*);
bool allocate_enemy_actor_address(EnemyScripts&,u32 id,u32& token);
}

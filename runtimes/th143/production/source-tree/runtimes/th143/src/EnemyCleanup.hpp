#pragma once
#include "AnmState.hpp"
#include <array>

namespace th143 {
// Addresses identify owned regions in the session, as in ANM/ECL state. A host
// may retain released storage for auditing, but must report every release.
struct EnemyCleanupMemory {
    virtual ~EnemyCleanupMemory()=default;
    virtual bool read_enemy_memory(u32,void*,u32)=0;
    virtual bool write_enemy_memory(u32,const void*,u32)=0;
    virtual bool release_enemy_storage(u32,bool array)=0;
    virtual bool find_enemy_visual(u32 handle,u32& token)=0;
};
bool cleanup_enemy_visual(u32 handle,EnemyCleanupMemory&);
bool cleanup_graphic_collection(u32 self,EnemyCleanupMemory&); //40cf10
bool cleanup_ecl_owner(u32 self,EnemyCleanupMemory&); //41d410
bool cleanup_enemy_actor(u32 self,u32 manager,EnemyCleanupMemory&,bool release_self=false); //41f2d0/41d9f0
bool reset_enemies(u32 manager,const std::array<u32,6>& resources,
                   const std::array<u32,2>& animation_heads,EnemyCleanupMemory&); //419a60
bool cleanup_effect_resources(u32 owner,const std::array<u32,2>& animation_heads,EnemyCleanupMemory&); //41aa40
}

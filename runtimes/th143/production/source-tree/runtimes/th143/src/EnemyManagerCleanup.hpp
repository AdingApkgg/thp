#pragma once
#include "EnemyCleanup.hpp"
namespace th143 {
struct EnemyManagerCleanupHost:EnemyCleanupMemory {
    virtual bool reset_enemy_manager(u32 owner)=0;
    virtual bool remove_enemy_manager_callback(u32 callback)=0;
    // The existing resource-world unload owns4828e0,resource storage release
    // and clearing the manager slot; empty slots are valid.
    virtual bool unload_enemy_animation(u32 slot)=0;
};
//41ea20. The caller owns the final delete of the e8-byte manager itself.
bool cleanup_enemy_manager(AnmView owner,u32 self,u32& global_owner,EnemyManagerCleanupHost&);
}

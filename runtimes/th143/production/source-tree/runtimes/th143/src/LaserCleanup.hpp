#pragma once
#include "EnemyCleanup.hpp"

namespace th143 {
struct LaserCleanupMemory:EnemyCleanupMemory {
    virtual bool remove_laser_callback(u32)=0;
    virtual bool destroy_laser(u32)=0;
};
// 438ce0. Beam-specific virtual destructors remain explicit services.
bool cleanup_laser_manager(u32 self,u32& current,LaserCleanupMemory&);
}

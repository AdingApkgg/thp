#pragma once
#include "Scheduler.hpp"
#include "AnmWorld.hpp"
namespace th143 {
// 436aa0: callback removal, deferred animation retirement and global clear.
// The caller owns the final498-byte storage release.
bool cleanup_cheat_owner(AnmView,u32& global_owner,Scheduler&,SchedulerHost&,AnmWorld&);
}

#pragma once
#include "AnmState.hpp"
namespace th143 {
struct LaserKind2CleanupHost {
 virtual ~LaserKind2CleanupHost()=default;
 virtual bool laser_cleanup_read(u32,void*,u32)=0;
 virtual bool laser_cleanup_release(u32,bool array)=0;
};
// 43f760. External path nodes are freed in list order; only the two buffer
// pointers are cleared. The embedded head's next pointer remains unchanged.
bool cleanup_laser_kind2(AnmView,LaserKind2CleanupHost&);
}

#pragma once
#include "LaserCancel.hpp"
namespace th143 {
struct LaserRectangleCancelHost:LaserCancelHost {
 virtual bool laser_cancel_rectangle_virtual(u32 beam,u32 position,u32 size,float angle,i32& result)=0;
};
// Actual4392d0. Both position and size remain live guest pointers. The
// manager's scratch copies precede traversal; mode1 and inactive beams skip.
bool cancel_lasers_rectangle(u32 manager,u32 position,u32 size,float angle,LaserRectangleCancelHost&,i32& result,u32 budget=100000);
}

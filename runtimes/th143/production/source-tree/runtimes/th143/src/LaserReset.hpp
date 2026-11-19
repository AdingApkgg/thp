#pragma once
#include "LaserFullCancel.hpp"
namespace th143 {
struct LaserResetHost:LaserFullCancelHost {virtual bool laser_reset_write(u32,const void*,u32)=0;};
bool reset_lasers(u32 manager,LaserResetHost&,i32& result,u32 budget=100000);
}

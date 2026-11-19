#pragma once
#include "AnmState.hpp"
namespace th143 {
struct LaserFullCancelHost {
 virtual bool laser_full_read(u32,void*,u32)=0;
 virtual bool laser_full_virtual(u32 beam,i32 kind,bool items,i32& result)=0;
};
bool cancel_lasers_full(u32 manager,i32 kind,bool items,LaserFullCancelHost&,i32& result,u32 budget=100000);
}

#pragma once
#include "AnmState.hpp"
namespace th143 {
struct LaserCancelHost {
    virtual ~LaserCancelHost()=default;
    virtual bool laser_cancel_read(u32,void*,u32)=0;
    virtual bool laser_cancel_write(u32,const void*,u32)=0;
    virtual bool laser_cancel_virtual(u32 beam,u32 position,float radius,i32 kind,bool items,i32& result)=0;
};
//439490. Position stays a live guest pointer passed to each beam. The manager
//retains its initial position; next is captured before virtual table+24.
bool cancel_lasers_circle(u32 manager,u32 position,float radius,i32 kind,bool items,LaserCancelHost&,i32& result,u32 budget=100000);
}

#pragma once
#include "AnmState.hpp"
namespace th143 {
struct LaserManagerHost:AnmTimerHost {
    virtual bool laser_read(u32 token,void*,u32 bytes)=0;
    virtual bool laser_write(u32 token,const void*,u32 bytes)=0;
    virtual bool laser_virtual(u32 token,u32 slot,bool has_argument,u32 argument,i32& result)=0;
    virtual bool laser_release(u32 token)=0;
};
bool update_laser_manager(u32 self,LaserManagerHost&,u32 budget=100000); //438e80
bool frame_laser_manager(u32 self,u32 root_flags,float& rate,LaserManagerHost&); //438fb0
bool draw_laser_manager(u32 self,LaserManagerHost&,u32 budget=100000); //438f80
bool frame_draw_laser_manager(u32 self,u32 root_flags,LaserManagerHost&); //439020
}

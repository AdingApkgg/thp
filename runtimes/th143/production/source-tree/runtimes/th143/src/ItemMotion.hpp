#pragma once
#include "ItemPool.hpp"
#include "AnmVm.hpp"

namespace th143 {
struct ItemPlayer {
    std::array<float,3> position{};
    std::array<float,4> collect{},magnet{},focused_magnet{};
    float speed=0;
    u32 state=0,keys=0;
    bool attract_all=false;
};
struct ItemMotionHost : AnmTimerHost {
    virtual bool bind(AnmView,u32 self,i32 type)=0;
    virtual bool animate(AnmView)=0;
    virtual bool collect(i32 type,const std::array<float,3>& position)=0;
    virtual bool position_visual(u32,const std::array<float,3>&)=0;
    virtual bool retire_visual(u32 handle,i32 signal){return handle==0;}
    virtual void homing_type(i32 type){}
};
// Original4350e0 delayed5, falling1, free-flight2, homing3/4 and timers.
// Pickup services and external-handle fade must be supplied by the world.
bool item_manager_step(ItemPool&,const ItemPlayer&,float elapsed,ItemMotionHost&);
}

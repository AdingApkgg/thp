#pragma once
#include "GameOwnerRuntime.hpp"
#include "AnmPool.hpp"
namespace th143 {
struct GameAnimationPoolDevice {
    virtual ~GameAnimationPoolDevice()=default;
    virtual bool animation_pool_vertex_format(u32)=0;
};
//47f3c0's forty callbacks use the application's Scheduler and game allocator.
class GameAnimationPool final:public AnmPoolHost,private SchedulerHost {
public:
    GameAnimationPool(GameFrameRuntime& frames,GameOwnerServices& storage,GameAnimationPoolDevice& device):frames(frames),storage(storage),device(device){}
    bool register_pool_callback(u32 entry,i32 priority,bool draw,u32 owner)override;
    bool set_pool_vertex_format(u32 value)override{return device.animation_pool_vertex_format(value);}
    bool allocate_pool_fallback(u32&,AnmView&)override{return false;}
private:
    bool invoke(u32,u32,u32&)override{return false;}
    bool release_callback(u32)override{return false;}
    GameFrameRuntime& frames;GameOwnerServices& storage;GameAnimationPoolDevice& device;
};
}

#pragma once
#include "RootFrame.hpp"

namespace th143 {
struct BackgroundWorker {
    std::array<u8,0x1c> data{};
    AnmView view(){return {data.data()};}
};
struct RootFactoryGlobals {u32 root=0,presentation=0;};
struct RootFactoryHost {
    virtual ~RootFactoryHost()=default;
    virtual bool allocate_root(u32& token)=0;
    virtual bool evict_managed_textures()=0;
    virtual bool wait_worker(u32 handle,u32 milliseconds,u32& result)=0;
    virtual bool sleep_worker(u32 milliseconds)=0;
    virtual bool close_worker(u32 handle)=0;
    virtual bool launch_worker(u32 entry,u32 argument,u32 flags,u32& thread_id,u32& handle)=0;
};
bool stop_background_worker(BackgroundWorker&,RootFactoryHost&,u32 wait_budget=100000); //403e90
bool start_root_worker(BackgroundWorker&,RootFactoryHost&); //444ad0
bool create_root(RootState&,BackgroundWorker&,RootFactoryGlobals&,u32 mode,RootFactoryHost&); //432f00
}

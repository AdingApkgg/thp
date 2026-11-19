#pragma once
#include "AnmInstance.hpp"

namespace th143 {
struct AnmStorageHost {
    virtual ~AnmStorageHost()=default;
    virtual bool release_buffer(u32 token)=0;
    virtual bool release_instance(u32 token)=0;
    virtual bool prepare_instance_release(u32 token,AnmView){return true;}
};
// Original483740 ordinary primary-list update and483d50 external retirement.
// Drawing lists are rebuilt for35 layers, preserving pre-update next fetches.
// Secondary/overlay scheduling and regular pool free-list slots are separate.
struct AnmManager {
    std::array<u32,35> draws{};
    u32 visited=0,retired=0;
    u32 failed_self=0;
    bool update(AnmRegistry&,AnmVmHost&,AnmStorageHost&);
    bool retire(AnmRegistry&,u32 self,AnmVmHost&,AnmStorageHost&);
};
}

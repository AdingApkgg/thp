#pragma once
#include "StageInit.hpp"
namespace th143 {
struct StageCleanupGlobals {u32 game_flags=0,current=0,previous=0;};
struct StageCleanupHost {
    virtual ~StageCleanupHost()=default;
    virtual bool read_stage_cleanup_memory(u32,void*,u32)=0;
    virtual bool write_stage_cleanup_memory(u32,const void*,u32)=0;
    virtual bool remove_stage_callback(u32)=0;
    virtual bool release_stage_storage(u32,bool array)=0;
    virtual bool cleanup_stage_collection(u32)=0;
    virtual bool unload_stage_animation(u32 slot)=0;
};
//40d290. The caller owns scalar release of the Stage object itself.
bool cleanup_stage(StageState&,u32 self,StageCleanupGlobals&,StageCleanupHost&);
}

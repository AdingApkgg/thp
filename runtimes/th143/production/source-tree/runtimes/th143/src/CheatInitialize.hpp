#pragma once
#include "CheatScene.hpp"
#include "Scheduler.hpp"
namespace th143 {
struct CheatInitializeHost:SchedulerHost {
    virtual bool cheat_resource(u32 file,const char* name,u32& token)=0;
    virtual bool cheat_callback_storage(u32& token,u8& fill)=0;
    virtual bool cheat_resource_error()=0;
};
// 436a20: actual Scheduler record construction and insertion. A missing
// resource is the native handled result -1; host failures return false.
bool initialize_cheat_owner(AnmView,u32 self,Scheduler&,CheatInitializeHost&,i32& result);
}

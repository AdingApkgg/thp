#pragma once
#include "CheatInitialize.hpp"
#include "CheatCleanup.hpp"
namespace th143 {
struct CheatFactoryHost:CheatInitializeHost {
    virtual bool cheat_owner_storage(u32& token,AnmView&)=0;
    virtual bool cheat_owner_view(u32 token,AnmView&)=0;
    virtual bool cheat_owner_release(u32 token)=0;
};
bool create_cheat_owner(u32& global_owner,u32& result,Scheduler&,AnmWorld&,CheatFactoryHost&); //436ba0
bool destroy_cheat_owner(u32 token,u32& global_owner,Scheduler&,AnmWorld&,CheatFactoryHost&); //436bf0
bool destroy_current_cheat_owner(u32& global_owner,Scheduler&,AnmWorld&,CheatFactoryHost&); //436c10
}

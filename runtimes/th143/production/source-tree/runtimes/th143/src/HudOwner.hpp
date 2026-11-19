#pragma once
#include "HudLoad.hpp"
#include "Scheduler.hpp"
#include "AnmWorld.hpp"
namespace th143 {
struct HudOwnerGlobals {
    HudLoadGlobals scene;
    u32 owner=0,game_flags=0,scene_resource=0;
};
struct HudOwnerHost:HudLoadHost,SchedulerHost {
    virtual bool hud_front_resource(u32& resource)=0;
    virtual bool hud_callback_storage(u32& token,u8& fill)=0;
    virtual bool hud_owner_storage(u32& token,AnmView&)=0;
    virtual bool hud_owner_view(u32 token,AnmView&)=0;
    virtual bool hud_message_view(u32 token,AnmView&)=0;
    virtual bool hud_release_storage(u32 token,bool array)=0;
    //4828e0 then scalar free of slot6, before the slot is cleared.
    virtual bool hud_release_scene_resource(u32 token)=0;
};
void construct_hud_owner(AnmView); //42c390, publication belongs to factory
bool initialize_hud_owner(AnmView,u32 self,HudOwnerGlobals&,Scheduler&,HudOwnerHost&,i32& result); //42c3c0
bool cleanup_hud_message(AnmView,AnmWorld&); //42c010
bool reset_hud_scene(AnmView,HudOwnerGlobals&,Scheduler&,AnmWorld&,HudOwnerHost&); //42cb00
bool cleanup_hud_owner(AnmView,HudOwnerGlobals&,Scheduler&,AnmWorld&,HudOwnerHost&); //42ce90
bool create_hud_owner(HudOwnerGlobals&,u32& result,Scheduler&,AnmWorld&,HudOwnerHost&); //42d1b0
bool destroy_hud_owner(u32,HudOwnerGlobals&,Scheduler&,AnmWorld&,HudOwnerHost&); //42d220
bool destroy_current_hud_owner(HudOwnerGlobals&,Scheduler&,AnmWorld&,HudOwnerHost&); //42d240
}

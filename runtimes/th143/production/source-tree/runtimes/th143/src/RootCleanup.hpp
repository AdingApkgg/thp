#pragma once
#include "RootFrame.hpp"
#include "ResourceCleanup.hpp"

namespace th143 {
enum class RootOwner:u32 {game,replay,previous_replay,menu,hud,player,player_aux,bullets,items,lasers,scores,cheats,enemies,effects,extra,count};
struct RootCleanupGlobals {
    u32 root=0,presentation=0,game_flags=0,application_state=0,current_scene=0,previous_scene=0,deaths=0,scene_descriptor=0;
    u32 auxiliary1=0,auxiliary2=0,shutdown=0,clear_color=0;
    float rate=1.f;
    std::array<u32,static_cast<u32>(RootOwner::count)> owners{};
    u32& owner(RootOwner k){return owners[static_cast<u32>(k)];}
};
struct RootCleanupHost {
    virtual ~RootCleanupHost()=default;
    virtual bool save_before_cleanup()=0;
    virtual bool cleanup_transition()=0;
    virtual bool independent_graphics()=0;
    // Components clear their own globals at the exact original service point.
    virtual bool destroy_root_owner(RootOwner,u32,RootCleanupGlobals&)=0;
    virtual bool reset_root_enemies(u32)=0;
    virtual bool cleanup_root_effects(u32)=0;
    virtual bool preserve_gameplay(RootCleanupGlobals&)=0;
    virtual bool remove_root_callback(u32)=0;
    virtual bool release_root_storage(u32)=0;
    virtual bool fade_root_audio()=0;
    virtual bool pause_root_audio()=0;
};
bool cleanup_root(RootState&,RootCleanupGlobals&,RootCleanupHost&); //432a30
bool destroy_current_root(RootState&,RootCleanupGlobals&,RootCleanupHost&); //432f80
}

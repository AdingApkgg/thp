#pragma once
#include "AnmWorld.hpp"
#include "PauseMenu.hpp"
#include "PlayerState.hpp"

namespace th143 {
struct SceneCleanupGlobals {
    u32 game_flags=0,player=0,menu=0,hud=0,saved_shots=0,saved_message=0;
};
struct SceneCleanupHost {
    virtual ~SceneCleanupHost()=default;
    virtual bool remove_callback(u32)=0;
    virtual bool deactivate_callback(u32)=0;
    virtual bool release_storage(u32 token,bool array)=0;
    virtual bool destroy_scene_choice(u32)=0;
    virtual bool destroy_message(u32)=0;
    virtual bool unload_message_resource()=0;
};
// Destruction marks registered animations; their actual retirement remains
// in the two animation update passes, as in the original executable.
bool cleanup_player(PlayerState&,AnmWorld&,SceneCleanupGlobals&,SceneCleanupHost&);
bool cleanup_pause_menu(PauseMenu&,SceneCleanupGlobals&,SceneCleanupHost&);
bool cleanup_hud_message(AnmView,AnmWorld&,SceneCleanupGlobals&,SceneCleanupHost&);
bool cleanup_hud(AnmView,AnmWorld&,SceneCleanupGlobals&,SceneCleanupHost&);
}

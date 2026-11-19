#pragma once
#include "AnmState.hpp"
namespace th143 {
struct HudMessageGlobals {
    u32 player_state=0,root_mode=0,root_flags=0,dialog=0;
    u32 game_flags=0,config=0,application_state=0,presentation=0,transition=0;
};
struct HudMessageHost:AnmTimerHost {
    virtual bool create_hud_message(i32 id)=0;
    virtual bool update_hud_message_owner(u32 token,i32& result)=0;
    virtual bool hud_message_view(u32 token,AnmView&)=0;
    virtual bool destroy_hud_message_owner(u32 token)=0;
    virtual bool hud_dialog_view(u32 token,AnmView&)=0;
    virtual bool request_hud_dialog_result()=0;
    virtual bool destroy_hud_dialog(u32 token)=0;
};
//42e4b0/42ece0. Message and dialog owners are separate services; caller passes
// the live globals and the complete SaveData view for notification ownership.
bool update_hud_message(AnmView hud,AnmView save,HudMessageGlobals&,HudMessageHost&);
}

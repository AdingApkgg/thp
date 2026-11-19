#pragma once
#include "FailureMenu.hpp"
#include "CheatAnimation.hpp"
namespace th143 {
struct PauseMenuInput:FailureMenuGlobals {
    bool root_update_enabled=false;
    i32 root_time=0;
};
struct PauseControlHost:FailureMenuHost {
    virtual bool resume_pause_audio()=0;
    virtual bool pause_message_owner(u32 token,bool paused)=0;
    virtual bool pause_exit_fade()=0;
};
bool begin_pause_menu(PauseMenu&,SaveData&,GameOverGlobals&,AnmWorld&,AnmOverlay&,AnmView hud,PauseControlHost&); //448290
bool resume_pause_menu(PauseMenu&,GameOverGlobals&,AnmWorld&,AnmView hud,PauseControlHost&); //448640
//447db0/4486c0. Replay/equipment/map ownership in substates8..12 is supplied
// by other_substate; missing owners fail instead of consuming the transition.
i32 pause_menu_frame(PauseMenu&,SaveData&,GameOverGlobals&,PauseMenuInput&,AnmWorld&,AnmOverlay&,AnmView hud,PauseControlHost&);
}

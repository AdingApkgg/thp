#pragma once
#include "GameOver.hpp"
#include "MenuCursor.hpp"

namespace th143 {
struct FailureMenuGlobals {
    u32 fresh=0,repeated=0,score=0,high_score=0,scene=0,deaths=0,retry_credits=0;
};
struct FailureMenuHost:GameOverHost {
    virtual bool menu_sound(u32)=0;
    virtual bool hint_text(u32 handle,const u8* encoded)=0;
    // Save/replay/name/equipment/map submenus retain separate ownership.
    virtual bool other_substate(PauseMenu&,u32 substate)=0;
};
// 447db0 failure state2 ->449c60. Returns-2 for an unavailable state/service.
i32 failure_menu_frame(PauseMenu&,SaveData&,GameOverGlobals&,FailureMenuGlobals&,AnmWorld&,AnmOverlay&,AnmView hud,FailureMenuHost&);
}

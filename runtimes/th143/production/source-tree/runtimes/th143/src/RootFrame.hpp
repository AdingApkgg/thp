#pragma once
#include "AnmState.hpp"
#include <array>

namespace th143 {
struct RootState {
    static constexpr u32 bytes=0x9c;
    std::array<u8,bytes> data{};
    AnmView view(){return {data.data()};}
    void construct(){data.fill(0);}
};
struct RootFrameGlobals {
    u32 game_flags=0,config=0x180,keys=0,application_state=0,presentation=0;
    u32 score=0,high_score=0,scene=0,high_score_scene=0,frames=0,scene_frames=0;
    bool previous_dialog=false;u32 previous_dialog_flags=0;
};
struct RootFrameHost:AnmTimerHost {
    virtual bool start_or_restart(RootState&,RootFrameGlobals&)=0;
    virtual bool notice(u32 kind,u32 duration,u32 message)=0;
    virtual bool replay_exit()=0;
    virtual bool erase_previous_dialog()=0;
    virtual bool animate_backgrounds()=0;
};
// 430de0, including unsigned score delta and the original signed comparisons.
void root_score_display(AnmView hud,RootFrameGlobals&);
// 433720->432fd0 live frame; unsupported startup services return-2, never skip.
i32 root_frame(RootState&,AnmView hud,RootFrameGlobals&,RootFrameHost&);
}

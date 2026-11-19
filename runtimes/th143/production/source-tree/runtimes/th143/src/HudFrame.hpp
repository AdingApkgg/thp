#pragma once
#include "AnmSignal.hpp"
namespace th143 {
struct HudFrameHost:AnmTimerHost,AnmSignalHost {
    virtual bool hud_owner(u32 global,AnmView&)=0;
    virtual bool hud_actor(u32 token,AnmView&)=0;
    virtual bool hud_sound(u32 id)=0;
    bool animation_signal_callback(u32,AnmView,i32)override{return false;}
};
//42d260/42ecd0: countdown, boss rings, life icons, direction indicator and timers.
bool update_hud(AnmView,AnmWorld&,HudFrameHost&);
}

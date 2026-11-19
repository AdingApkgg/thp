#pragma once
#include "AnmState.hpp"

namespace th143 {
struct HudSceneHost {
    virtual ~HudSceneHost()=default;
    virtual bool hud_scene_signal(u32 handle,i32 signal)=0;
};
// 431770: signal the two retained HUD animations, clear the live-message gate
// and reset its timer, retaining an already initialized rate and flags.
bool begin_hud_scene(AnmView,HudSceneHost&);
}

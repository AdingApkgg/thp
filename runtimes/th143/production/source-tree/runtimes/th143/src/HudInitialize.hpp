#pragma once
#include "AnmWorld.hpp"

namespace th143 {
struct HudInitializeGlobals {u32 game_flags=0,selection=0;};
struct HudInitializeHost {
    virtual ~HudInitializeHost()=default;
    virtual bool hud_callback_read(u32 token,u32& flags)=0;
    virtual bool hud_callback_write(u32 token,u32 flags)=0;
    virtual bool hud_ascii_resource(u32& token)=0;
};
// Original42c690. HUD98/9c retain VM addresses, while50/54 retain handles.
bool initialize_hud(AnmView,HudInitializeGlobals&,AnmWorld&,HudInitializeHost&);
}

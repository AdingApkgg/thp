#pragma once
#include "PlayerState.hpp"
#include "AnmWorld.hpp"
namespace th143 {
struct PlayerResetHost {
    virtual ~PlayerResetHost()=default;
    virtual bool reset_lives(i32 lives,u32 fragments)=0;
    virtual bool reset_visual_callback(u32 entry,AnmView,i32 signal)=0;
};
// Original44c440, used by the root startup/restart path. This rebuilds the
// intrusive shot free list; it preserves shot payloads and collision regions.
bool reset_player(PlayerState&,u32 self,i32 lives,u32 fragments,AnmWorld&,PlayerResetHost&);
}

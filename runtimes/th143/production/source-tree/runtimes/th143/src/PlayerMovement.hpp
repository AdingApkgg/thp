#pragma once
#include "PlayerState.hpp"
#include "AnmState.hpp"

namespace th143 {
struct PlayerMovementInput {
    u32 keys=0;
    bool gameplay=false,alternate_focus=false;
    i32 equipment=0;
    float elapsed=1.f;
};
struct PlayerMovementHost {
    virtual ~PlayerMovementHost()=default;
    virtual bool bind_player_visual(PlayerState&,i32 script)=0;
    virtual bool create_focus(i32 script,u32& handle)=0;
    virtual AnmView visual(u32 handle)=0;
    virtual bool signal_visual(u32 handle,i32 signal)=0;
    virtual bool option_callback(PlayerState&,u32 offset,u32 entry)=0;
};
// Original44cb40, including focus ownership, integer motion, animation changes,
// position history and all eight option slots. The caller owns frame timers.
bool player_movement(PlayerState&,const PlayerMovementInput&,PlayerMovementHost&);
}

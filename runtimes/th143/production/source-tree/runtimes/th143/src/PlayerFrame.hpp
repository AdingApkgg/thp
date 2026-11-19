#pragma once
#include "PlayerMovement.hpp"
#include "ScalarInterpolation.hpp"

namespace th143 {
struct PlayerFrameGlobals {
    PlayerMovementInput input;
    bool message=false;
    u32 root_flags=0,game_mode=0;
    std::array<float,3> wind{};
    i32 lives=0;u32 life_fragments=0,bombs=0,bomb_fragments=0,deaths=0,death_flag=0;
    std::array<i32,12> sound_ids{-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1};
    std::array<u32,12> sound_parameters{};
};
struct PlayerFrameHost:PlayerMovementHost,AnmTimerHost {
    virtual bool set_frame_rate(float)=0;
    virtual bool animate_player(PlayerState&)=0;
    virtual bool effect(i32 script,const std::array<float,3>& position)=0;
    virtual bool cancel_circle(const std::array<float,3>& position,float radius,i32 kind)=0;
    virtual bool cancel_lasers(const std::array<float,3>& position,float radius,i32 kind,bool items)=0;
    virtual bool cancel_all_lasers(i32 kind,bool items)=0;
    virtual bool lives_changed(i32 lives,u32 fragments)=0;
    virtual bool bombs_changed(u32 bombs,u32 fragments)=0;
    virtual bool game_over(bool replay)=0;
    virtual bool retire_visual(u32 handle)=0;
    virtual bool shoot(PlayerState&,PlayerFrameGlobals&)=0;
    virtual bool update_shots(PlayerState&)=0;
};
// Original44e3d0 ->44d540. Returns original1/3, or-2 for an unavailable service.
i32 player_frame(PlayerState&,PlayerFrameGlobals&,PlayerFrameHost&);
}

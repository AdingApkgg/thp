#pragma once
#include "PlayerInit.hpp"
#include "AnmVm.hpp"

namespace th143 {
struct PlayerShootingConfig {
    u32 self=0x6a000000,keys=0;
    bool alternate=false;
    i32 equipment=0,power=0,power_step=100;
    std::array<i32,2> viewport_origin{128,16};
};
struct PlayerShootingHost:AnmTimerHost {
    virtual bool create_shot_visual(u32 resource,i32 script,u32& handle)=0;
    virtual AnmView shot_visual(u32 handle)=0;
    virtual bool retire_shot_visual(u32 handle)=0;
    virtual bool shot_vertices(AnmView,std::array<std::array<float,2>,4>&)=0;
    virtual bool shot_sound(i32 id,float x)=0;
    virtual bool shot_callback(u32 entry,bool spawn,PlayerState&,u32 offset,i32 time,i32& result)=0;
};
// Original451130/451040/450a70, and451500/451230. Nonzero specialized
// SHT callbacks remain explicit host services; ordinary pl00a uses none.
bool player_shoot(PlayerState&,PlayerShotData&,const PlayerShootingConfig&,PlayerShootingHost&);
bool player_update_shots(PlayerState&,PlayerShotData&,const PlayerShootingConfig&,PlayerShootingHost&);
}

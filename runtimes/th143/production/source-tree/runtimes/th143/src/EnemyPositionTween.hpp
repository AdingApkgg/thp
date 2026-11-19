#pragma once
#include "ActorState.hpp"
#include "AnmInterpolation.hpp"
namespace th143 {
// ECL401/402 common-mode position tween and42a3d0's float3 state layout.
// Per-axis mode selection remains rejected until independently bound.
bool start_enemy_position_tween(ActorState&,bool relative,i32 duration,i32 mode,float x,float y,AnmTimerHost&);
bool sample_enemy_position_tween(AnmView,AnmTimerHost&,std::array<u32,3>&);
}

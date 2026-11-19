#pragma once
#include "ActorState.hpp"
#include "ScalarInterpolation.hpp"
#include "Rng.hpp"
namespace th143 {
bool enemy_random_movement(ActorState&,bool relative,i32 duration,i32 mode,float speed,float aim_x,Rng&,AnmTimerHost&);
bool enemy_direct_movement(ActorState&,float elapsed,AnmTimerHost&);
float enemy_position_quantize(float value);
}

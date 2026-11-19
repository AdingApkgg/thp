#pragma once
#include "ActorState.hpp"
#include "ScalarInterpolation.hpp"
namespace th143 {
//422fd4/4230ae absolute or relative polar movement setters.
bool set_enemy_polar(ActorState&,bool relative,float angle,float speed);
bool start_enemy_polar_tween(ActorState&,bool relative,i32 duration,i32 mode,float angle,float speed,AnmTimerHost&);
}

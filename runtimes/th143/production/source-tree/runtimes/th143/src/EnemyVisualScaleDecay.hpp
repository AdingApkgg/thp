#pragma once
#include "AnmState.hpp"
namespace th143 {
struct EnemyVisualScaleDecayHost {
 virtual ~EnemyVisualScaleDecayHost()=default;
 virtual AnmView enemy_scale_animation(u32 handle)=0;
};
// 42a0b0, installed by ECL516 selector80. Rate is the actual global at call.
bool decay_enemy_visual_scale(AnmView,float rate,EnemyVisualScaleDecayHost&,i32& result);
}

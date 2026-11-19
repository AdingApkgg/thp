#pragma once
#include "AnmState.hpp"
namespace th143 {
struct EnemyAnimationAlphaHost {
 virtual ~EnemyAnimationAlphaHost()=default;
 virtual bool find_alpha_animation(u32 handle,AnmView&)=0;
};
// ECL328 through4270d0 and42b120, including missing/stale handle clearing.
i32 enemy_animation_alpha(AnmView actor,Vm&,VmHost&,EnemyAnimationAlphaHost&,u32 rate=0x4e40b0);
}

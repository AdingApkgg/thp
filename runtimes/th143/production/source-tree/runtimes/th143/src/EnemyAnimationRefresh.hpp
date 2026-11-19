#pragma once
#include "AnmState.hpp"
namespace th143 {
struct EnemyAnimationRefreshHost {
 virtual ~EnemyAnimationRefreshHost()=default;
 virtual bool refresh_retire(u32 offset,u32& handle)=0;
 virtual bool refresh_create(i32 selector,i32 script,i32 layer,u32& handle)=0;
 virtual bool refresh_find(u32 offset,u32& handle,AnmView& image)=0;
 virtual bool refresh_clear_flag2(u32 offset,u32& handle)=0;
};
// ECL313: recreate a selected handle using the actor's current animation base.
i32 enemy_animation_refresh(AnmView actor,Vm&,VmHost&,EnemyAnimationRefreshHost&);
}

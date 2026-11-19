#pragma once
#include "PlayerState.hpp"
#include "SoundQueue.hpp"
namespace th143 {
struct EnemyPlayerSwapHost {
 virtual ~EnemyPlayerSwapHost()=default;
 virtual bool enemy_swap_sound(u32 id,float x)=0;
 virtual bool enemy_swap_visual(u32 resource,i32 script,const std::array<float,3>& position)=0;
};
// 637 selector6 /42a120, including real41dd00 fixed-point movement semantics.
bool swap_enemy_player(AnmView enemy,PlayerState&,AnmView shadow_option,SoundQueue&,EnemyPlayerSwapHost&,i32& result);
}

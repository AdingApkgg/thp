#pragma once
#include "PlayerState.hpp"
namespace th143 {
// Local rectangle x spans[0,length] for44e990/44eb70 and
//[-length/2,length/2] for44ed10; local y spans[-width/2,width/2].
// Probe returns0/1/2(outside/hit/graze) without lifecycle/guard checks.
i32 player_rotated_rectangle_probe(PlayerState&,const std::array<float,3>& origin,float length,float width,float angle,bool centered=false); //44eb70
i32 player_rotated_rectangle_collision(PlayerState&,bool hud_blocked,const std::array<float,3>& origin,float length,float width,float angle,bool forced,PlayerHitHost&,bool centered=false); //44e990/44ed10
}

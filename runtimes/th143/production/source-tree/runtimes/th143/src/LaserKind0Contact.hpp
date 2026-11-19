#pragma once
#include "AnmVm.hpp"
namespace th143 {
struct LaserKind0ContactHost:AnmTimerHost {
 virtual bool laser_player_rectangle(const std::array<float,3>&,float length,float width,float angle,bool forced,i32&)=0;
 virtual bool laser_player_position(std::array<float,3>&)=0;
 virtual bool laser_player_cancel(u32 token,const std::array<float,3>& position,const std::array<float,3>& size,float angle,i32 kind,bool items)=0;
 virtual bool laser_player_graze(const std::array<float,3>&)=0;
};
bool contact_laser_kind0(AnmView,u32 token,bool forced,LaserKind0ContactHost&);
}

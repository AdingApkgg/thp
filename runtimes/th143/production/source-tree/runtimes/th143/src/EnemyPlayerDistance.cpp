#include "EnemyPlayerDistance.hpp"
#include <cmath>
namespace th143 {
bool enemy_player_distance(AnmView actor,i32 id,float x,float y,float& value){
 if(id!=-9944)return false;
 const float dx=actor.floating(0x44)-x,dy=actor.floating(0x48)-y;
 const float xx=dx*dx,yy=dy*dy,sum=xx+yy;
 value=float(std::sqrt(double(sum)));return true;
}
}

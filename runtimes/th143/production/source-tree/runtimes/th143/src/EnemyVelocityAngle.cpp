#include "EnemyVelocityAngle.hpp"
#include <cmath>
namespace th143 {
bool enemy_velocity_angle(AnmView actor,i32 id,float& value){
    if(id!=-9958)return false;
    const float x=actor.floating(0x78),y=actor.floating(0x7c);
    if(!std::isfinite(x)||!std::isfinite(y))return false;
    value=float(std::atan2(double(y),double(x)));return true;
}
}

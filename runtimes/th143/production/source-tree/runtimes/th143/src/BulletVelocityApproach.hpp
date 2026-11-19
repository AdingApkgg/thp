#pragma once
#include "BulletMotion.hpp"
#include <functional>
namespace th143 {
void bind_bullet_velocity_approach_services(BulletMotionHost&,std::function<bool(BulletView,float&)>,std::function<bool(i32)>);
bool start_bullet_velocity_approach_acceleration(BulletView,u32,BulletMotionHost&,u32);
i32 bullet_velocity_approach_acceleration(BulletView,BulletMotionHost&);
}

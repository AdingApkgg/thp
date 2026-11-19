#pragma once
#include "BulletMotion.hpp"
#include <functional>
namespace th143 {
void start_bullet_boundary_bounce(BulletView,u32 row);
i32 update_bullet_boundary_bounce(BulletView,float manager_width,float manager_height,const std::function<bool(i32)>&);
}

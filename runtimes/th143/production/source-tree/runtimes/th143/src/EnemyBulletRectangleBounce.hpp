#pragma once
#include "AnmState.hpp"
#include "BulletPool.hpp"
#include <functional>
namespace th143 {
bool enemy_bullet_rectangle_bounce(AnmView,BulletPool&,const std::function<bool(i32)>&,i32&);
}

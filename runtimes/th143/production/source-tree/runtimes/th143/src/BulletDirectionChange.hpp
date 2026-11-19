#pragma once
#include "BulletMotion.hpp"
#include "Rng.hpp"
#include <array>
#include <functional>
namespace th143 {
struct BulletDirectionServices {Rng* random=nullptr;std::function<bool(const std::array<float,3>&,float&)> aim;std::function<bool(i32)> sound;};
void bind_bullet_direction_change(BulletMotionHost&,BulletDirectionServices);
bool start_bullet_direction_change(BulletView,u32,BulletMotionHost&,u32);
i32 bullet_direction_change(BulletView,BulletMotionHost&);
}

#pragma once
#include "BulletMotion.hpp"
#include <functional>
namespace th143 {
using BulletSpatialSound=std::function<bool(i32,float)>;
bool start_bullet_sound_transform(BulletView,u32 row,const BulletSpatialSound&);
void bind_bullet_sound_transform(BulletMotionHost&,BulletSpatialSound);
bool dispatch_bullet_sound_transform(BulletView,u32 row,BulletMotionHost&);
}

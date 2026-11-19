#pragma once
#include "BulletMotion.hpp"
#include <functional>
namespace th143 {
bool start_bullet_transform_cancel(BulletView,u32 row,const std::function<bool(BulletView,i32)>&);
void bind_bullet_transform_cancel(BulletMotionHost&,std::function<bool(BulletView,i32)>);
bool dispatch_bullet_transform_cancel(BulletView,u32 row,BulletMotionHost&);
}

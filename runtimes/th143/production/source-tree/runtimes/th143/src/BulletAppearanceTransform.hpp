#pragma once
#include "BulletFactory.hpp"
#include <functional>
namespace th143 {
void bind_bullet_appearance_transform(BulletMotionHost&,std::function<bool(BulletView,u32)>);
bool dispatch_bullet_appearance_transform(BulletView,u32,BulletMotionHost&);
bool change_bullet_appearance(BulletView,u32,u32,u32,BulletFactoryHost&);
}

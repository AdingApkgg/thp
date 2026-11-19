#pragma once
#include "BulletMotion.hpp"
#include <functional>
namespace th143 {
using BulletSpawnLaunch=std::function<bool(const u8*,u32)>;
using BulletSpawnCancel=std::function<bool(BulletView,i32)>;
bool start_bullet_spawn_transform(BulletView,u32 row,const BulletSpawnLaunch&,const BulletSpawnCancel&);
void bind_bullet_spawn_transform(BulletMotionHost&,BulletSpawnLaunch,BulletSpawnCancel);
bool dispatch_bullet_spawn_transform(BulletView,u32 row,BulletMotionHost&);
}

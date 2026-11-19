#pragma once
#include "BulletMotionDay1.hpp"
#include "EnemySpawn.hpp"
#include <functional>
namespace th143 {
using BulletEnemySpawn=std::function<bool(u32,const EnemySpawn&)>;
bool start_bullet_enemy_transform(BulletView,u32 row,const BulletEnemySpawn&);
void bind_bullet_enemy_transform(BulletMotionHost&,BulletEnemySpawn);
bool dispatch_bullet_enemy_transform(BulletView,u32 row,BulletMotionHost&);
}

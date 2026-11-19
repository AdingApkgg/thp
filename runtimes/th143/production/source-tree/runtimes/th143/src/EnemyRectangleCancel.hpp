#pragma once
#include "EnemyCancel.hpp"
namespace th143 {
bool cancel_enemy_rectangle(u32,const std::array<float,3>&,const std::array<float,3>&,float,i32,BulletCancelGlobals&,BulletCancelHost&,EnemyCancelHost&);
}

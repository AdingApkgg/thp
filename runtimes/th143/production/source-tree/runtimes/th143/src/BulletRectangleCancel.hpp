#pragma once
#include "BulletCancel.hpp"
namespace th143 {
struct BulletRectangleCancelHost:BulletCancelHost {virtual bool cancel_enemy_rectangle(const std::array<float,3>&,const std::array<float,3>&,float,i32)=0;};
//417650: scans all2000 slots, applies rotated camera and playfield intersections.
bool cancel_bullets_rectangle(u32,const std::array<float,3>&,const std::array<float,3>&,float,i32,const float&,BulletCancelGlobals&,AnmWorld&,BulletRectangleCancelHost&);
}

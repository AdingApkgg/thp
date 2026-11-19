#pragma once
#include "BulletBoundaryBounce.hpp"
#include "BulletPool.hpp"
namespace th143 {
void bind_bullet_boundary_bounce(BulletMotionHost&,const BulletPool&,std::function<bool(i32)>);
i32 dispatch_bullet_boundary_bounce(BulletView,BulletMotionHost&);
}

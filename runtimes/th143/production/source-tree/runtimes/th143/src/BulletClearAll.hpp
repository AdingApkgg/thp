#pragma once
#include "BulletCancel.hpp"
#include "BulletPool.hpp"
namespace th143 {
//417a30 traverses all2000 physical slots,including delayed/non-list bullets.
bool clear_all_bullets(BulletPool&,const float&,BulletCancelGlobals&,AnmWorld&,BulletCancelHost&);
}

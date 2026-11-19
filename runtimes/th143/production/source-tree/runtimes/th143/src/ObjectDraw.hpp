#pragma once
#include "BulletPool.hpp"
#include "ItemPool.hpp"
#include "PlayerDraw.hpp"
namespace th143 {
//413b10->413730: six draw lists, two embedded VMs per bullet.
bool draw_bullet_objects(BulletPool&,u32 root_flags,PlayerDrawHost&);
//436000->435ec0: regular/delayed slots, including off-screen item indicators.
bool draw_item_objects(ItemPool&,u32 root_flags,PlayerDrawHost&);
}

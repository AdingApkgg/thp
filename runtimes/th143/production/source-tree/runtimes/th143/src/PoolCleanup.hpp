#pragma once
#include "AnmWorld.hpp"
#include "BulletPool.hpp"
#include "ItemPool.hpp"
#include "ScorePopups.hpp"

namespace th143 {
struct PoolCleanupGlobals {u32 bullets=0,items=0,scores=0;};
struct PoolCleanupHost {
    virtual ~PoolCleanupHost()=default;
    virtual bool remove_pool_callback(u32)=0;
    virtual bool release_pool_array(u32)=0;
};
bool cleanup_bullet_pool(BulletPool&,AnmWorld&,PoolCleanupGlobals&,PoolCleanupHost&);
bool cleanup_item_pool(ItemPool&,PoolCleanupGlobals&,PoolCleanupHost&);
bool cleanup_score_popups(ScorePopups&,PoolCleanupGlobals&,PoolCleanupHost&);
}

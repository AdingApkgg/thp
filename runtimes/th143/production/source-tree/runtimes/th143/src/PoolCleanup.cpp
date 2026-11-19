#include "PoolCleanup.hpp"

namespace th143 {
namespace {
bool mark_resource(AnmWorld& world,u32 resource){
    for(u32 node:{world.instances.registry.primary_head,world.instances.registry.secondary_head}){
        u32 budget=0;while(node){
            auto i=world.instances.registry.nodes.find(node-0x570);if(i==world.instances.registry.nodes.end()||++budget>world.states.size())return false;
            auto vm=i->second;node=vm.get(0x574);if(vm.get(0x30)==resource)vm.put(0x1c,vm.get(0x1c)|0x20);
        }
    }return true;
}
bool release_field(AnmView view,u32 at,PoolCleanupHost& host){
    const u32 token=view.get(at);if(token&&!host.release_pool_array(token))return false;view.put(at,0);return true;
}
}
bool cleanup_bullet_pool(BulletPool& pool,AnmWorld& world,PoolCleanupGlobals& g,PoolCleanupHost& host){
    if(!host.remove_pool_callback(pool.get(8))||!host.remove_pool_callback(pool.get(12))||!mark_resource(world,pool.get(0x9bf6cc)))return false;
    g.bullets=0;
    // 48b0f4 destroys all2001 elements from the last slot to the first.
    for(u32 i=BulletPool::count+1;i;--i){AnmView bullet{pool.data.data()+BulletPool::first+(i-1)*BulletPool::stride};
        if(!release_field(bullet,0xba8,host)||!release_field(bullet,0x5dc,host))return false;
    }return true;
}
bool cleanup_item_pool(ItemPool& pool,PoolCleanupGlobals& g,PoolCleanupHost& host){
    if(!host.remove_pool_callback(pool.get(8))||!host.remove_pool_callback(pool.get(12)))return false;g.items=0;
    for(u32 i=ItemPool::count;i;--i){AnmView item{pool.data.data()+ItemPool::first+(i-1)*ItemPool::stride};
        if(!release_field(item,0xb90,host)||!release_field(item,0x5c4,host))return false;
    }return true;
}
bool cleanup_score_popups(ScorePopups& scores,PoolCleanupGlobals& g,PoolCleanupHost& host){
    if(!host.remove_pool_callback(scores.get(8))||!host.remove_pool_callback(scores.get(12)))return false;g.scores=0;
    return release_field({scores.data.data()},0x5cc,host);
}
}

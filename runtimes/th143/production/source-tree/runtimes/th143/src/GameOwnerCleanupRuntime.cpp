#include "GameOwnerCleanupRuntime.hpp"
namespace th143 {
namespace {
struct Region {u32 base,bytes;u8* data;};
template<class F> bool visit_owner_regions(GameOwnerRuntime& o,F&& f){
    for(auto r:{Region{GameOwnerRuntime::player_self,u32(o.player.data.size()),o.player.data.data()},
        {GameOwnerRuntime::equipment_self,u32(o.equipment.data.size()),o.equipment.data.data()},
        {GameOwnerRuntime::input_self,u32(o.input.manager.data.size()),o.input.manager.data.data()},
        {BulletPool::token_base,BulletPool::bytes,o.bullets.data.data()},
        {ItemPool::token_base,ItemPool::bytes,o.items.data.data()},
        {GameOwnerRuntime::laser_self,u32(o.lasers.size()),o.lasers.data()},
        {ScorePopups::token,ScorePopups::bytes,o.scores.data.data()}})if(f(r))return true;
    return false;
}
}
bool GameOwnerCleanupRuntime::read_retained(u32 p,void* out,u32 n){
    if(visit_owner_regions(owners,[&](Region r){if(p<r.base||std::uint64_t(p)+n>std::uint64_t(r.base)+r.bytes)return false;std::memcpy(out,r.data+p-r.base,n);return true;}))return true;
    return owners.read(p,out,n);
}
bool GameOwnerCleanupRuntime::write_retained(u32 p,const void* in,u32 n){
    if(visit_owner_regions(owners,[&](Region r){if(p<r.base||std::uint64_t(p)+n>std::uint64_t(r.base)+r.bytes)return false;std::memcpy(r.data+p-r.base,in,n);return true;}))return true;
    return owners.write(p,in,n);
}
bool GameOwnerCleanupRuntime::deactivate_callback(u32 p){if(!p)return true;auto cb=frames.scheduler.at(p);if(!cb.data)return false;cb.put(4,cb.get(4)&~2u);return true;}
bool GameOwnerCleanupRuntime::recording(u32& owner){
    if(owner!=GameOwnerRuntime::input_self||!(owners.created&4)||!game_manager_cleanup(owners.input.manager,owner,owner,*this))return false;
    owners.created&=~4u;return true;
}
bool GameOwnerCleanupRuntime::player(u32 flags,u32& owner,u32& saved){
    if(owner!=GameOwnerRuntime::player_self||!(owners.created&1))return false;
    SceneCleanupGlobals g;g.game_flags=flags;g.player=owner;g.saved_shots=saved;
    if(!cleanup_player(owners.player,animations,g,*this))return false;
    owner=g.player;saved=g.saved_shots;owners.created&=~1u;return true;
}
bool GameOwnerCleanupRuntime::equipment(u32& owner){
    if(owner!=GameOwnerRuntime::equipment_self||!(owners.created&2)||!cleanup_player_auxiliary(owners.equipment.view(),owner,*this))return false;
    owners.created&=~2u;return true;
}
bool GameOwnerCleanupRuntime::bullets(u32& owner){
    if(owner!=BulletPool::token_base||!(owners.created&8))return false;PoolCleanupGlobals g;g.bullets=owner;
    if(!cleanup_bullet_pool(owners.bullets,animations,g,*this))return false;owner=g.bullets;owners.created&=~8u;return true;
}
bool GameOwnerCleanupRuntime::items(u32& owner){
    if(owner!=ItemPool::token_base||!(owners.created&16))return false;PoolCleanupGlobals g;g.items=owner;
    if(!cleanup_item_pool(owners.items,g,*this))return false;owner=g.items;owners.created&=~16u;return true;
}
bool GameOwnerCleanupRuntime::lasers(u32& owner){
    if(owner!=GameOwnerRuntime::laser_self||!(owners.created&32)||!cleanup_laser_manager(owner,owner,*this))return false;
    owners.created&=~32u;return true;
}
bool GameOwnerCleanupRuntime::scores(u32& owner){
    if(owner!=ScorePopups::token||!(owners.created&64))return false;PoolCleanupGlobals g;g.scores=owner;
    if(!cleanup_score_popups(owners.scores,g,*this))return false;owner=g.scores;owners.created&=~64u;return true;
}
}

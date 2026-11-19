#include "EnemyBulletTransformReset.hpp"
#include "AnmState.hpp"
namespace th143 {
bool reset_enemy_bullet_transforms(BulletPool& pool,i32& result){
 auto valid_node=[](u32 p){return p>=BulletPool::token_base&&std::uint64_t(p)+8<=std::uint64_t(BulletPool::token_base)+BulletPool::bytes;};
 auto next=[&](u32 p,u32& out){if(!p){out=0;return true;}if(!valid_node(p))return false;out=pool.get(BulletPool::offset(p)+4);return true;};
 u32 node=pool.get(0x80),following;if(!next(node,following))return false;pool.put(0x9bf6c0,node);pool.put(0x9bf6c4,following);u32 visited=0;
 while(node){
  if(!valid_node(node)||++visited>BulletPool::count)return false;const u32 p=pool.get(BulletPool::offset(node));if(!p)break;
  if(p<BulletPool::bullet(0)||p>BulletPool::bullet(BulletPool::count-1))return false;auto b=AnmView{pool.data.data()+BulletPool::offset(p)};b.put(0xc20,8);b.put(0xc04,0);
  node=pool.get(0x9bf6c4);pool.put(0x9bf6c0,node);if(!next(node,following))return false;pool.put(0x9bf6c4,following);
 }
 result=0;return true;
}
}

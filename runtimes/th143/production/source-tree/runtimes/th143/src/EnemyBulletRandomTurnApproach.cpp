#include "EnemyBulletRandomTurnApproach.hpp"
#include "AnmState.hpp"
namespace th143 {
bool enemy_bullet_random_turn_approach(BulletPool& pool,Rng& rng,i32& result){
 u32 node=pool.get(0x80),visited=0;pool.put(0x9bf6c0,node);pool.put(0x9bf6c4,node?pool.get(BulletPool::offset(node)+4):0);
 while(node){
  if(++visited>BulletPool::count)return false;const u32 p=pool.get(BulletPool::offset(node));if(p<BulletPool::bullet(0)||p>BulletPool::bullet(BulletPool::count-1))return false;
  AnmView b{pool.data.data()+BulletPool::offset(p)};const float speed=rng.unit()+real(0x3e4ccccd);
  b.put(0xc78,1);b.put(0xc64,60);b.put(0xc58,0xc7c34f80);b.put(0xc74,0x200000);b.put(0xc54,word(speed));
  const float turn=rng.signed_unit()*real(0x3c2b92a6);b.put(0xca4,1);b.put(0xc90,60);b.put(0xc80,0);b.put(0xc84,word(turn));b.put(0xca0,8);
  node=pool.get(0x9bf6c4);pool.put(0x9bf6c0,node);pool.put(0x9bf6c4,node?pool.get(BulletPool::offset(node)+4):0);
 }
 result=0;return true;
}
}

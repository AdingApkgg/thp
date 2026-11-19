#include "BulletEnemyTransform.hpp"
#include <map>
namespace th143 {
namespace {std::map<BulletMotionHost*,BulletEnemySpawn> bindings;}
bool start_bullet_enemy_transform(BulletView b,u32 row,const BulletEnemySpawn& spawn){
 if(!spawn)return false;EnemySpawn descriptor;
 for(u32 i=0;i<3;++i)descriptor.position[i]=b.floating(0xbc0+i*4);
 descriptor.health=10000;
 for(u32 i=0;i<4;++i){descriptor.inherited[i]=b.get(row+0x10+i*4);descriptor.inherited[4+i]=b.get(row+i*4);}
 if(!spawn(b.get(row+0x28),descriptor))return false;
 b.put(0xc20,b.get(0xc20)+1);return true;
}
void bind_bullet_enemy_transform(BulletMotionHost& h,BulletEnemySpawn s){if(s)bindings[&h]=std::move(s);else bindings.erase(&h);}
bool dispatch_bullet_enemy_transform(BulletView b,u32 row,BulletMotionHost& h){const auto i=bindings.find(&h);return i!=bindings.end()&&start_bullet_enemy_transform(b,row,i->second);}
}

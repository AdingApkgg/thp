#include "EnemyBulletRectangleBounce.hpp"
#include "DirectionVector.hpp"
namespace th143 {
namespace {
float reflect(float angle,float axis){const float pi=real(0x40490fdb),tau=real(0x40c90fdb);float delta=axis-angle;if(delta>pi)angle+=tau;else if(angle-axis>pi)angle-=tau;delta=axis-angle;float value=delta+axis;u32 count=0;while(value>pi){value-=tau;if(count++>32)break;}while(real(0xc0490fdb)>value){value+=tau;if(count++>32)break;}return value;}
}
bool enemy_bullet_rectangle_bounce(AnmView actor,BulletPool& pool,const std::function<bool(i32)>& sound,i32& result){
 const float left=actor.floating(0x33c)+actor.floating(0x44),right=actor.floating(0x340)+actor.floating(0x44),top=actor.floating(0x344)+actor.floating(0x48),bottom=actor.floating(0x348)+actor.floating(0x48);
 u32 node=pool.get(0x80),visited=0;pool.put(0x9bf6c0,node);pool.put(0x9bf6c4,node?pool.get(BulletPool::offset(node)+4):0);
 while(node){if(++visited>BulletPool::count)return false;const u32 p=pool.get(BulletPool::offset(node));if(p<BulletPool::bullet(0)||p>BulletPool::bullet(BulletPool::count-1))return false;AnmView b{pool.data.data()+BulletPool::offset(p)};
  const float previous_x=b.floating(0xbc0)-b.floating(0xbcc)*2.f,previous_y=b.floating(0xbc4)-b.floating(0xbd0)*2.f;
  if(previous_x>=left-8.f&&right+8.f>=previous_x&&previous_y>=top-8.f&&bottom+8.f>=previous_y){bool changed=false;
   if(left>b.floating(0xbc0)&&previous_x>=left){b.put(0xbdc,word(reflect(b.floating(0xbdc),real(0xbfc90fdb))));b.put(0xbc0,word(left*2.f-b.floating(0xbc0)));changed=true;}
   if(b.floating(0xbc0)>right&&right>=previous_x){b.put(0xbdc,word(reflect(b.floating(0xbdc),real(0xbfc90fdb))));b.put(0xbc0,word(right*2.f-b.floating(0xbc0)));changed=true;}
   if(top>b.floating(0xbc4)&&previous_y>=top){b.put(0xbdc,word(reflect(b.floating(0xbdc),0.f)));b.put(0xbc4,word(top*2.f-b.floating(0xbc4)));changed=true;}
   if(b.floating(0xbc4)>bottom&&bottom>=previous_y){b.put(0xbdc,word(reflect(b.floating(0xbdc),0.f)));b.put(0xbc4,word(bottom*2.f-b.floating(0xbc4)));changed=true;}
   if(changed){DirectionVector v;if(!direction_vector(b.floating(0xbdc),b.floating(0xbd8),v))return false;b.put(0xbcc,word(v.x));b.put(0xbd0,word(v.y));if(signed_word(b.get(0xc1c))>=0&&!sound(signed_word(b.get(0xc1c))))return false;}
  }
  node=pool.get(0x9bf6c4);pool.put(0x9bf6c0,node);pool.put(0x9bf6c4,node?pool.get(BulletPool::offset(node)+4):0);
 }
 result=0;return true;
}
}

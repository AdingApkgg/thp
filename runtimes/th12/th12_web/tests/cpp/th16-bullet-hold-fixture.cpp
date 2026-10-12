#include "../../cpp/game/BulletTh16.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static BulletState b;static AnmSprite sprite;static float rate;static u32 events[16],count;
struct Services:Th16BulletStepServices{
 i32 collision(BulletState&)override{events[count++]=1;return 0;}
 i32 animation(AnmVm&)override{events[count++]=2;return 0;}
 bool sound(i32)override{return true;}
};
API(begin_case) i32 begin_case(float r,i32 duration,i32 mode,float x,float y,float angle,u32 active,i32 index,i32 concurrent,i32 grace){
 b={};rate=r;b.position={x,y,.1f};b.velocity={-1.25f,2.5f,.125f};b.speed=2.25f;b.angle=angle;b.flags=3;b.state=1;b.collision_delay=2;b.offscreen_grace=grace;b.th16_size=1.5f;sprite={};sprite.width=17;sprite.height=36;b.vm.sprite=&sprite;
 b.transform_index=index;b.transform_sound=-1;b.active_transforms=active;b.motion[0].timer.set(active?16:0,&rate);b.motion[0].timer.previous=active?15:0;b.motion[6].timer.previous=0;
 auto& t=b.th16_transforms[index];t.opcode=0x100;t.p=duration;t.q=mode;t.concurrent=concurrent;
 b.auxiliary_timer.previous=0;b.auxiliary_timer.current=17;b.auxiliary_timer.fractional=17.5f;b.auxiliary_timer.rate=&rate;count=0;Services services;
 return bullet_th16_start_transforms(b,&rate,nullptr,nullptr,nullptr,&services);
}
API(step) i32 step(){count=0;Services s;const i32 result=bullet_th16_step(b,rate,s);if(result==-1)events[count++]=3;return result;}
API(value) u32 value(u32 n){const u32 v[]={float_bits(b.position.x),float_bits(b.position.y),float_bits(b.position.z),float_bits(b.velocity.x),float_bits(b.velocity.y),float_bits(b.velocity.z),b.active_transforms,u32(b.transform_index),u32(b.collision_delay),u32(b.offscreen_grace),u32(b.auxiliary_timer.previous),u32(b.auxiliary_timer.current),float_bits(b.auxiliary_timer.fractional),u32(b.motion[0].timer.previous),u32(b.motion[0].timer.current),float_bits(b.motion[0].timer.fractional),u32(b.motion[6].timer.previous),u32(b.motion[6].timer.current),float_bits(b.motion[6].timer.fractional),u32(b.motion[6].duration)};return v[n];}
API(event_count) u32 event_count(){return count;}
API(event) u32 event(u32 n){return events[n];}

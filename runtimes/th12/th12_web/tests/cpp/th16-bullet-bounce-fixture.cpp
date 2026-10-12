#include "../../cpp/game/BulletTh16.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static BulletState b;static AnmSprite sprite;static float rate;static Vec2 bounds;static u32 events[16][2],count;
struct Services:Th16BulletStepServices{
 i32 collision(BulletState&)override{events[count][0]=1;events[count++][1]=0;return 0;}
 i32 animation(AnmVm&)override{events[count][0]=2;events[count++][1]=0;return 0;}
 bool sound(i32 id)override{events[count][0]=4;events[count++][1]=u32(id);return true;}
 Vec2 bounce_bounds()const override{return bounds;}
};
API(begin_case) i32 begin_case(float r,i32 mask,i32 limit,float speed,float x,float y,float angle,float bw,float bh,u32 active,i32 index,i32 concurrent,i32 sound){
 b={};rate=r;bounds={bw,bh};b.position={x,y,.1f};b.velocity={-1.25f,2.5f,.125f};b.speed=2.25f;b.angle=angle;b.flags=3;b.state=1;b.collision_delay=2;b.offscreen_grace=64;b.th16_size=1.5f;b.extra=9;sprite={};sprite.width=17;sprite.height=36;b.vm.sprite=&sprite;
 b.transform_index=index;b.transform_sound=sound;b.active_transforms=active;b.motion[0].timer.set(active?16:0,&rate);b.motion[0].timer.previous=active?15:0;
 auto& t=b.th16_transforms[index];t.opcode=64;t.a=speed;t.b=280;t.c=320;t.p=limit;t.q=mask;t.concurrent=concurrent;b.th16_transforms[index+1].opcode=32768;b.th16_transforms[index+1].p=37;
 b.auxiliary_timer.previous=0;b.auxiliary_timer.current=17;b.auxiliary_timer.fractional=17.5f;b.auxiliary_timer.rate=&rate;count=0;Services services;
 return bullet_th16_start_transforms(b,&rate,nullptr,nullptr,nullptr,&services);
}
API(step) i32 step(){count=0;Services s;const auto result=bullet_th16_step(b,rate,s);if(result==-1){events[count][0]=3;events[count++][1]=0;}return result;}
API(value) u32 value(u32 n){const auto& slot=b.motion[8];const u32 v[]={float_bits(b.position.x),float_bits(b.position.y),float_bits(b.position.z),float_bits(b.velocity.x),float_bits(b.velocity.y),float_bits(b.velocity.z),float_bits(b.speed),float_bits(b.angle),b.active_transforms,u32(b.transform_index),u32(b.collision_delay),u32(b.offscreen_grace),u32(b.auxiliary_timer.previous),u32(b.auxiliary_timer.current),float_bits(b.auxiliary_timer.fractional),u32(b.motion[0].timer.previous),u32(b.motion[0].timer.current),float_bits(b.motion[0].timer.fractional),float_bits(slot.a),float_bits(slot.vector.x),float_bits(slot.vector.y),u32(slot.count),u32(slot.limit),u32(slot.duration),u32(b.extra)};return v[n];}
API(event_count) u32 event_count(){return count;}
API(event) u32 event(u32 n,u32 f){return events[n][f];}

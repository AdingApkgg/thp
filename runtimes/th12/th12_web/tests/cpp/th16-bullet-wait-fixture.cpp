#include "../../cpp/game/BulletTh16.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static BulletState b;static float rate;static u32 events[16][3],count;static const Vec3 player{-15.5f,400.f,0};
static void record(u32 kind,u32 id=0,u32 x=0){const u32 row[]={kind,id,x};std::memcpy(events[count++],row,sizeof row);}
struct Services:Th16BulletStepServices{
 i32 collision(BulletState&)override{record(1);return 0;}
 i32 animation(AnmVm&)override{record(2);return 0;}
 bool sound(i32 id)override{record(4,id);return true;}
 bool positional_sound(i32 id,float x)override{record(5,id,float_bits(x));return true;}
 Vec3 player_position()const override{return player;}
};
API(begin_case) i32 begin_case(float r,i32 duration,i32 index,i32 concurrent,u32 active,float accel,float direction,float angle,i32 sound,i32 audio){
 b={};rate=r;b.position={7.125f,9.25f,.1f};b.velocity={-1.25f,2.5f,.125f};b.speed=2.25f;b.angle=angle;b.flags=3;b.state=1;b.collision_delay=2;b.offscreen_grace=10000;
 b.transform_index=index;b.transform_sound=sound;b.active_transforms=active;b.motion[0].timer.previous=active?15:0;b.motion[0].timer.current=active?16:0;b.motion[0].timer.fractional=active?16.f:0.f;b.motion[0].timer.rate=&rate;b.motion[2].vector.z=.125f;
 if(audio){auto& t=b.th16_transforms[index++];t.opcode=0x80000000u;t.p=duration;t.concurrent=concurrent;}
 auto& t=b.th16_transforms[index];t.opcode=4;t.a=accel;t.b=direction;t.c=.25f;t.p=duration;t.concurrent=concurrent;
 b.motion[3].timer.previous=0;b.motion[2].timer.previous=0;b.auxiliary_timer.previous=0;b.auxiliary_timer.current=17;b.auxiliary_timer.fractional=17.5f;b.auxiliary_timer.rate=&rate;count=0;Services services;return bullet_th16_start_transforms(b,&rate,nullptr,nullptr,&player,&services);
}
API(step) i32 step(){count=0;Services s;const i32 result=bullet_th16_step(b,rate,s);if(result==-1)record(3);return result;}
API(value) u32 value(u32 n){const u32 values[]={float_bits(b.position.x),float_bits(b.position.y),float_bits(b.position.z),float_bits(b.velocity.x),float_bits(b.velocity.y),float_bits(b.velocity.z),float_bits(b.speed),float_bits(b.angle),b.active_transforms,u32(b.transform_index),u32(b.collision_delay),u32(b.auxiliary_timer.previous),u32(b.auxiliary_timer.current),float_bits(b.auxiliary_timer.fractional),u32(b.motion[0].timer.previous),u32(b.motion[0].timer.current),float_bits(b.motion[0].timer.fractional),float_bits(b.motion[0].vector.z),u32(b.motion[2].timer.previous),u32(b.motion[2].timer.current),float_bits(b.motion[2].timer.fractional),float_bits(b.motion[2].a),float_bits(b.motion[2].b),float_bits(b.motion[2].vector.x),float_bits(b.motion[2].vector.y),float_bits(b.motion[2].vector.z),u32(b.motion[2].duration),u32(b.motion[3].timer.previous),u32(b.motion[3].timer.current),float_bits(b.motion[3].timer.fractional)};return values[n];}
API(event_count) u32 event_count(){return count;}
API(event) u32 event(u32 n,u32 f){return events[n][f];}


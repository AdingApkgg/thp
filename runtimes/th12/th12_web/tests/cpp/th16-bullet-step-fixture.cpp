#include "../../cpp/game/BulletTh16.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static BulletState b;static AnmSprite sprite;static float rate;static u32 events[8],count;static i32 animation_result;
struct Services:Th16BulletStepServices{ i32 collision(BulletState&)override{events[count++]=1;return 0;}i32 animation(AnmVm&)override{events[count++]=2;return animation_result;} };
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(run_case) i32 run_case(u32 state,float r,i32 animation,u32 flags,i32 lifetime,i32 delay,i32 grace,i32 integer,u32 etex,i32 age,float fraction,const float* values){
 b={};b.motion[0].timer.previous=0;sprite={};sprite.width=17;sprite.height=36;b.vm.sprite=&sprite;b.th16_size=1.5f;b.state=i16(state);b.flags=flags;
 b.position={values[0],values[1],values[2]};b.velocity={values[3],values[4],values[5]};b.lifetime.current=lifetime;b.collision_delay=delay;b.offscreen_grace=grace;b.vm.integers[0]=integer;
 if(etex>=2){b.active_transforms=1;b.transform_index=1;b.motion[0].timer.previous=33;b.motion[0].timer.current=age;b.motion[0].timer.fractional=fraction;b.motion[0].timer.rate=&rate;}
 if(etex){b.th16_transforms[0].opcode=1;b.speed=2.25f;b.angle=.3f;}
 rate=r;b.auxiliary_timer.current=17;b.auxiliary_timer.fractional=17.5f;b.auxiliary_timer.rate=&rate;count=0;animation_result=animation;
 Services services;const i32 result=bullet_th16_step(b,r,services);if(result==-1)events[count++]=3;return result;
}
API(value) u32 value(u32 n){const u32 v[]={float_bits(b.position.x),float_bits(b.position.y),float_bits(b.position.z),u32(b.collision_delay),u32(b.offscreen_grace),u32(b.state),u32(b.auxiliary_timer.previous),u32(b.auxiliary_timer.current),float_bits(b.auxiliary_timer.fractional),float_bits(b.velocity.x),float_bits(b.velocity.y),float_bits(b.velocity.z),b.active_transforms,u32(b.transform_index),u32(b.motion[0].timer.previous),u32(b.motion[0].timer.current),float_bits(b.motion[0].timer.fractional),float_bits(b.motion[0].vector.z)};return v[n];}
API(event_count) u32 event_count(){return count;}
API(event) u32 event(u32 n){return events[n];}

#include "../../cpp/game/BulletTh16.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static BulletState b;static u32 events[32],count;static i32 result;static AnmVm effect_vm;static float rate;
struct Services:Th16BulletCollisionServices{
 i32 probe(const BulletState& v)override{const bool circle=v.flags&0x10;Vec2 size=v.hitbox;if(v.flags&0x40){size.x*=v.th16_size;size.y*=v.th16_size;}const u32 words[]={0,u32(circle),float_bits(v.position.x),float_bits(v.position.y),float_bits(v.position.z),float_bits(size.x),circle?0u:float_bits(size.y)};for(auto word:words)events[count++]=word;return result;}
 bool effect(const Vec3& p,i32 script,const Vec3& velocity)override{const u32 words[]={1,u32(script),float_bits(p.x),float_bits(p.y),float_bits(p.z)};for(auto word:words)events[count++]=word;
  bullet_th16_hit_effect_setup(effect_vm,velocity,&rate);return true;
 }
 bool graze(const Vec3& p)override{const u32 words[]={2,float_bits(p.x),float_bits(p.y),float_bits(p.z)};for(auto word:words)events[count++]=word;return true;}
};
API(run_case) i32 run_case(u32 flags,i32 delay,i32 probe,i32 effect,float r,u32 nativeflags,float width){
 b={};effect_vm={};count=0;result=probe;rate=r;b.flags=flags;b.collision_delay=delay;b.state=1;b.cancel_effect=effect;b.vm.th13_native_flags=nativeflags;b.vm.pending_interrupt=9;b.vm.script_position={7,8,9};b.position={1.25f,-2.5f,.125f};b.velocity={1.25f,-.75f,.5f};b.hitbox={width,12};b.th16_size=1.5f;Services services;return bullet_th16_collision(b,rate,services);
}
API(value) u32 value(u32 n){const u32 values[]={b.flags,u32(b.state),u32(b.vm.pending_interrupt),b.vm.th13_native_flags,float_bits(b.vm.script_position.x),float_bits(b.vm.script_position.y),float_bits(b.vm.script_position.z)};return values[n];}
API(event_count) u32 event_count(){return count;}
API(event) u32 event(u32 n){return events[n];}
API(interp_word) u32 interp_word(u32 n){const auto& i=effect_vm.position_interpolation;if(n<12){const float* arrays[]={i.start,i.end,i.initial_tangent,i.final_tangent};return float_bits(arrays[n/3][n%3]);}const u32 words[]={u32(i.timer.previous),u32(i.timer.current),float_bits(i.timer.fractional),u32(i.duration),u32(i.mode)};return words[n-12];}

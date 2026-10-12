#include "../../cpp/game/BulletTh16.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static BulletState b;static float rate=1;
API(run_case) i32 run_case(u32 style,u32 color,u32 delayed){
 b={};Th16BulletEmitter e{};e.sprite=style;e.color=color;e.position={1,2,3};e.angle=.3f;e.spread=.5f;e.speed=2;e.slow_speed=1;e.count=e.layers=e.aim=1;e.flags=0x23;e.transform_sound=38;
 if(delayed){e.transforms[0].opcode=2;e.transforms[0].p=delayed;}
 Rng rng;BulletLaunch launch{};if(!bullet_th16_launch(e,0,0,0,rng,{},0,launch))return -2;
 return bullet_th16_bind_metadata(b,e,launch,&rate)?0:-2;
}
API(value) u32 value(u32 n){const u32 v[]={b.flags,u32(b.collision_delay),float_bits(b.position.x),float_bits(b.position.y),float_bits(b.position.z),float_bits(b.velocity.x),float_bits(b.velocity.y),float_bits(b.velocity.z),float_bits(b.speed),float_bits(b.angle),float_bits(b.hitbox.x),float_bits(b.hitbox.y),u32(b.offscreen_grace),u32(b.cancel_effect),u32(b.transform_index),u32(b.th16_script_state),b.active_transforms,b.emitter_flags,u32(b.state),u32(b.reserved_4c0),u32(b.transform_sound),u32(b.draw_group),float_bits(b.th16_size),u32(u16(b.sprite))|(u32(u16(b.color))<<16)};return v[n];}

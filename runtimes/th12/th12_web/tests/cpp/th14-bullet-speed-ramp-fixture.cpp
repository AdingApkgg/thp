#include "../../cpp/game/BulletState.hpp"
#include "../../cpp/game/BulletTh14.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
struct World:BulletEnvironment{u32 sounds=0;bool sound(i32,float,bool)override{++sounds;return false;}};
static World world;static BulletState bullet;
API(begin) i32 begin(u32 index,i32 duration,float rate,float angle,float acceleration){
 bullet={};world.rate=rate;world.player={60,400,0};world.sounds=0;bullet.position={-12.25f,70.5f,0};bullet.velocity={2.5f,-.125f,.25f};bullet.speed=2.75f;bullet.angle=.375f;
 bullet.motion[10].vector.z=.125f;bullet.transform_index=i32(index);bullet.transform_sound=38;
 auto& t=bullet.th14_transforms[index];t.a=acceleration;t.b=angle;t.c=.35f;t.p=duration;t.opcode=0x200000;return bullet_th14_start_transforms(bullet,world);
}
API(tick) i32 tick(){return bullet_th14_speed_ramp_tick(bullet,world);}
API(word) u32 word(u32 n){const auto& b=bullet;const auto& s=b.motion[10];const u32 v[]={b.active_transforms,u32(b.transform_index),float_bits(b.speed),float_bits(b.angle),float_bits(b.velocity.x),float_bits(b.velocity.y),float_bits(b.velocity.z),float_bits(s.a),float_bits(s.b),u32(s.timer.previous),u32(s.timer.current),float_bits(s.timer.fractional),u32(s.duration),float_bits(s.vector.x),float_bits(s.vector.y),float_bits(s.vector.z),world.sounds};return v[n];}

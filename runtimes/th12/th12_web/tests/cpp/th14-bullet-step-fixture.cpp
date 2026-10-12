#include "../../cpp/game/BulletState.hpp"
#include "../../cpp/game/BulletTh14.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
struct World:BulletEnvironment{u32 sounds=0;Rng rng;bool sound(i32,float,bool)override{++sounds;return false;}};
static World world;static BulletState bullet;
API(begin) i32 begin(i32 mode,i32 duration,float rate,float angle,float target){
 bullet={};world.rate=rate;world.player={60,400,0};world.sounds=0;world.rng={1234,0,0};world.th14_visual_rng=&world.rng;
 bullet.position={-12.25f,70.5f,0};bullet.velocity={2.5f,-.125f,.25f};bullet.speed=2.75f;bullet.angle=.375f;
 bullet.motion[9].a=1.5f;bullet.motion[9].b=-.2f;bullet.motion[9].vector={20,150,2};bullet.motion[3].b=.625f;bullet.transform_sound=38;
 auto& t=bullet.th14_transforms[0];t.a=angle;t.b=target;t.p=duration;t.q=2;t.r=mode;t.s=19;t.opcode=0x10;return bullet_th14_start_transforms(bullet,world);
}
API(tick) i32 tick(){return bullet_th14_step_tick(bullet,world);}
API(word) u32 word(u32 n){const auto& b=bullet;const auto& s=b.motion[3];const auto& saved=b.motion[9];const u32 v[]={b.active_transforms,u32(b.transform_index),float_bits(b.speed),float_bits(b.angle),float_bits(b.velocity.x),float_bits(b.velocity.y),float_bits(b.velocity.z),float_bits(s.a),float_bits(s.b),u32(s.timer.previous),u32(s.timer.current),float_bits(s.timer.fractional),u32(s.duration),u32(s.limit),u32(s.count),u32(b.th14_step_mode),u32(b.th14_step_extra),float_bits(saved.a),float_bits(saved.b),float_bits(saved.vector.x),float_bits(saved.vector.y),float_bits(saved.vector.z),u32(world.rng.seed),world.rng.calls,world.sounds};return v[n];}

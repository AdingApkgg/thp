#include "../../cpp/game/BulletState.hpp"
#include "../../cpp/game/BulletTh14.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
struct World:BulletEnvironment{u32 sounds=0;bool sound(i32,float,bool)override{++sounds;return false;}};
static World world;static BulletState bullet;
API(begin) i32 begin(i32 duration,float rate,float angle,float speed){
 bullet={};world.rate=rate;world.player={60,400,0};world.sounds=0;bullet.position={-12.25f,70.5f,3.25f};bullet.velocity={2.5f,-.125f,.25f};bullet.speed=2.75f;bullet.angle=.375f;
 auto& t=bullet.th14_transforms[0];t.a=angle;t.b=speed;t.p=duration;t.opcode=0x80000;return bullet_th14_start_transforms(bullet,world);
}
API(add_flags) void add_flags(){bullet.active_transforms|=9;}
API(tick) i32 tick(){return bullet_th14_polar_move_tick(bullet,world);}
API(word) u32 word(u32 n){const auto& b=bullet;const auto& s=b.motion[8];const u32 values[]={b.active_transforms,u32(b.transform_index),float_bits(b.position.x),float_bits(b.position.y),float_bits(b.position.z),float_bits(b.speed),float_bits(b.angle),float_bits(b.velocity.x),float_bits(b.velocity.y),float_bits(b.velocity.z),u32(s.timer.previous),u32(s.timer.current),float_bits(s.timer.fractional),float_bits(s.a),float_bits(s.b),float_bits(s.vector.x),float_bits(s.vector.y),float_bits(s.vector.z),u32(s.duration),world.sounds};return values[n];}

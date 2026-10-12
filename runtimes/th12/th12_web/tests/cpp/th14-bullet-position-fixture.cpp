#include "../../cpp/game/BulletState.hpp"
#include "../../cpp/game/BulletTh14.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
struct World:BulletEnvironment{u32 sounds=0;bool sound(i32,float,bool)override{++sounds;return false;}};
static World world;static BulletState bullet;
API(begin) i32 begin(i32 duration,float rate,u32 mode,u32 relative,float x,float y){
 bullet={};world.rate=rate;world.default_tangent={.125f,-.25f,.0625f};world.sounds=0;bullet.position={-12.25f,70.5f,3.25f};bullet.velocity={2.5f,-.125f,.25f};bullet.speed=2.75f;bullet.angle=.375f;
 auto& t=bullet.th14_transforms[0];t.a=x;t.b=y;t.p=duration;t.q=mode|(relative<<8);t.opcode=0x20000;return bullet_th14_start_transforms(bullet,world);
}
API(tick) i32 tick(){return bullet_th14_position_tick(bullet,world);}
API(word) u32 word(u32 n){const auto& b=bullet;const auto& s=b.motion[7];const auto& p=b.position_interpolation;
 const u32 values[]={b.active_transforms,u32(b.transform_index),float_bits(b.position.x),float_bits(b.position.y),float_bits(b.position.z),float_bits(b.speed),float_bits(b.angle),float_bits(b.velocity.x),float_bits(b.velocity.y),float_bits(b.velocity.z),u32(s.timer.previous),u32(s.timer.current),float_bits(s.timer.fractional),float_bits(s.a),float_bits(s.vector.x),float_bits(s.vector.y),float_bits(s.vector.z),u32(s.duration),u32(s.limit),float_bits(p.start[0]),float_bits(p.start[1]),float_bits(p.start[2]),float_bits(p.end[0]),float_bits(p.end[1]),float_bits(p.end[2]),float_bits(p.initial_tangent[0]),float_bits(p.initial_tangent[1]),float_bits(p.initial_tangent[2]),float_bits(p.final_tangent[0]),float_bits(p.final_tangent[1]),float_bits(p.final_tangent[2]),u32(p.timer.previous),u32(p.timer.current),float_bits(p.timer.fractional),u32(p.duration),u32(p.mode),world.sounds};return values[n];}

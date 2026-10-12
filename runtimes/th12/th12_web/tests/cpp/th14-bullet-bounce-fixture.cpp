#include "../../cpp/game/BulletState.hpp"
#include "../../cpp/game/BulletTh14.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
struct World:BulletEnvironment{u32 sounds=0;bool sound(i32,float,bool)override{++sounds;return false;}};
static World world;static BulletState bullet;
API(begin) i32 begin(i32 override,i32 mask,float x,float y,float angle,float speed,i32 limit){
 bullet={};world.rate=1;world.sounds=0;const Vec2 bounds[]={{0,0},{160,300},{0,300}};world.th14_bounce_bounds=bounds[override];
 bullet.position={x,y,3};bullet.velocity={2.5f,-.125f,.25f};bullet.speed=2.75f;bullet.angle=angle;bullet.transform_sound=38;
 bullet.motion[4].b=-.625f;bullet.motion[4].vector.z=.125f;
 auto& t=bullet.th14_transforms[0];t.a=speed;t.b=256;t.c=320;t.p=limit;t.q=mask;t.opcode=0x40;return bullet_th14_start_transforms(bullet,world);
}
API(tick) i32 tick(){return bullet_th14_bounce_tick(bullet,world);}
API(word) u32 word(u32 n){const auto& b=bullet;const auto& s=b.motion[4];const u32 v[]={b.active_transforms,u32(b.transform_index),float_bits(b.position.x),float_bits(b.position.y),float_bits(b.position.z),float_bits(b.velocity.x),float_bits(b.velocity.y),float_bits(b.velocity.z),float_bits(b.speed),float_bits(b.angle),float_bits(s.a),float_bits(s.b),float_bits(s.vector.x),float_bits(s.vector.y),float_bits(s.vector.z),u32(s.count),u32(s.limit),u32(s.duration),world.sounds};return v[n];}

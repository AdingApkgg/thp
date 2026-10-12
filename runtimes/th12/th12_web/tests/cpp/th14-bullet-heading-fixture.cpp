#include "../../cpp/game/BulletState.hpp"
#include "../../cpp/game/BulletTh14.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
struct World:BulletEnvironment{u32 sounds=0;bool sound(i32,float,bool)override{++sounds;return false;}};
static World world;static BulletState bullet;
API(begin) i32 begin(u32 index,u32 active,u32 concurrent,float angle,float speed){
 bullet={};world.rate=1;world.player={60,400,0};world.sounds=0;bullet.position={-12.25f,70.5f,0};bullet.velocity={2.5f,-.125f,.25f};bullet.speed=2.75f;bullet.angle=.375f;bullet.transform_index=i32(index);bullet.active_transforms=active;
 auto& t=bullet.th14_transforms[index];t.a=angle;t.b=speed;t.opcode=0x40000;t.concurrent=concurrent;return bullet_th14_start_transforms(bullet,world);
}
API(word) u32 word(u32 n){const auto& b=bullet;const u32 values[]={b.active_transforms,u32(b.transform_index),float_bits(b.speed),float_bits(b.angle),float_bits(b.velocity.x),float_bits(b.velocity.y),float_bits(b.velocity.z),world.sounds};return values[n];}

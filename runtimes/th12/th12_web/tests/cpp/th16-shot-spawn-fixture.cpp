#include "../../cpp/game/ShotTh16.hpp"
#include "../../cpp/game/ShotManager.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static Th16ShotSpawn shot;static Rng random;static std::array<u32,16> lasers;static float rate;
API(begin) i32 begin(i32 number,i32 kind,float angle,float speed,u32 focus,u32 family,u32 seed,float scale){
 shot={};shot.flags=0x80000000;shot.timer.flags=1;rate=scale;shot.timer.rate=&rate;random={u16(seed),0,17};lasers.fill(123);
 ShotSpec spec;spec.option=i8(number);spec.type=i8(kind);spec.damage=13;spec.hitbox={4.25,7.5};spec.angle=angle;spec.speed=speed;
 ShotPlayer player;player.power=399;player.power_step=100;player.focused=focus;for(i32 i=0;i<12;++i)player.options[i]={-321+i*777,50319-i*333,(i-5)*.75f,0};
 return shot_th16_spawn_prepare(shot,spec,family?0x10000:0,player,{7.25,400.5,1.25},random,lasers,&rate);
}
API(value) u32 value(u32 n){const u32 words[]={shot.flags,u32(shot.state),shot.packed,u32(shot.timer.previous),u32(shot.timer.current),float_bits(shot.timer.fractional),u32(shot.damage),float_bits(shot.hitbox.x),float_bits(shot.hitbox.y),random.seed,random.calls};return n<11?words[n]:lasers[n-11];}
API(movement) u32 movement(u32 n){const auto& m=shot.movement;const float words[]={m.position.x,m.position.y,m.position.z,m.speed,m.angle,m.velocity.x,m.velocity.y,m.velocity.z};return float_bits(words[n]);}

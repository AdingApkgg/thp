#include "../../cpp/game/BombReimuTh14.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static Th14ReimuOrb orb;static Enemy enemy;static EnemyLink link;static float rate;static bool present;
API(allocate) void* allocate(u32 size){return std::malloc(size);}
API(setup) void setup(const u32* w,u32 target,u32 manager,u32 flags,float x,float y,float speed,u32 index){
 orb={};orb.position={float_bits(w[0]),float_bits(w[1]),float_bits(w[2])};orb.anchor={float_bits(w[3]),float_bits(w[4]),float_bits(w[5])};orb.last_delta={float_bits(w[6]),float_bits(w[7]),float_bits(w[8])};
 orb.speed=float_bits(w[9]);orb.angle=float_bits(w[10]);orb.radius=float_bits(w[11]);orb.turn=float_bits(w[12]);orb.flags=w[13];orb.index=index;rate=speed;orb.timer.set(i32(w[15]),&rate);orb.timer.previous=i32(w[14]);orb.timer.fractional=float_bits(w[16]);
 enemy.state.flags=flags;enemy.state.current.position={x,y,0};link.value=&enemy;link.next=nullptr;orb.target=target?&enemy:nullptr;present=manager;
}
API(tick) void tick(){th14_reimu_orb_tick(orb,{12.25,300,3},&link,present,&rate);}
API(value) u32 value(u32 i){const u32 values[]={float_bits(orb.position.x),float_bits(orb.position.y),float_bits(orb.position.z),float_bits(orb.anchor.x),float_bits(orb.anchor.y),float_bits(orb.anchor.z),float_bits(orb.last_delta.x),float_bits(orb.last_delta.y),float_bits(orb.last_delta.z),float_bits(orb.speed),float_bits(orb.angle),float_bits(orb.radius),float_bits(orb.turn),orb.flags,u32(orb.timer.previous),u32(orb.timer.current),float_bits(orb.timer.fractional),u32(orb.target==&enemy)};return values[i];}

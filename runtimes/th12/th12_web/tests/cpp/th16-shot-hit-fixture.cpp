#include "../../cpp/game/ShotTh16.hpp"
#include "../../cpp/game/AnmVm.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static Th16ShotSpawn shot;static Th16DamageSources sources;static AnmVm vm;static i32 damage;
API(begin) i32 begin(u32 family,u32 index,u32 id,float speed,i32 hit,u32 flags,i32 pending){
 shot={};shot.flags=3;shot.packed=family?0x10000:0;shot.state=1;shot.animation=77;shot.damage_source=id;shot.damage=hit;shot.movement.position={7.25,300.5,1.25};shot.movement.speed=speed;shot.movement.angle=-.75;
 sources={};sources.records[id].words[0]=flags;vm={};vm.initialize();vm.flags=0x100;vm.flags2=0x2800;vm.position={11,22,33};vm.pending_interrupt=pending;return shot_th16_default_hit(shot,sources,vm,damage);
}
API(value) u32 value(u32 n){const u32 words[]={u32(damage),shot.flags,u32(shot.state),shot.animation,shot.damage_source,float_bits(shot.movement.position.x),float_bits(shot.movement.position.y),float_bits(shot.movement.position.z),float_bits(shot.movement.speed),float_bits(shot.movement.angle),sources.records[1].words[0],sources.records[256].words[0],u32(vm.pending_interrupt),float_bits(vm.position.x),float_bits(vm.position.y),float_bits(vm.position.z),vm.flags,vm.flags2};return words[n];}

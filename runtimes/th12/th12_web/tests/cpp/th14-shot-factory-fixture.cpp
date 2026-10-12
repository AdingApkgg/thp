#include "../../cpp/game/ShotManager.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include <new>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static ShtResource sht;static AnmResource anm;static AnmManager animations;
struct World:ShotWorld{}world;
static ShotManager manager(sht,anm,animations,world);static ShotSpec spec;static u32 creation_start;static AnmVm* vm;
API(spawn) i32 spawn(i32 option,float angle,i32 kind,u32 flags,u32 focus,float rate,u32 seed,i32 ox,i32 oy,float oa){
 manager.~ShotManager();new(&manager) ShotManager(sht,anm,animations,world);
 animations.clear();animations.rate=rate;animations.script_rng={54321,0,77};animations.visual_rng={u16(seed),0,123};anm.scripts.resize(7);
 for(auto& s:anm.scripts){s.bytes={};const u16 op=anm_th13_flag6;const u32 value=flags&1;const u8 prefix[]={u8(op),u8(op>>8),12,0,0,0,0,0,u8(value),0,0,0};s.bytes.assign(prefix,prefix+12);const u8 end[]={2,0,8,0,0,0,0,0,255,255,0,0,0,0,0,0};s.bytes.insert(s.bytes.end(),end,end+16);}
 manager.player={};manager.player.focused=focus;manager.player.power=120;manager.player.power_step=40;manager.player.options[option?option-1:0]={ox,oy,oa,0};manager.laser_active.fill(0);manager.last_error=0;
 for(u32 i=0;i<256;++i){manager.at(i)={};*manager.th14_bomb_area(i)={};}
 auto& shot=manager.at(255);shot.th14_shot_flags=flags;shot.timer.flags=0x80|(flags&1);shot.timer.rate=&animations.rate;shot.movement.velocity={1.25,-2.5,7.75};shot.movement.flags=0xf;
 spec={};spec.damage=19;spec.offset={.37,-.51};spec.hitbox={24,40};spec.angle=angle;spec.speed=8.125;spec.option=i8(option);spec.type=i8(kind);spec.animation=1;spec.sound=-1;creation_start=anm_creation_count();
 const i32 result=manager.spawn(spec,7,{-12.25,400.125,3});vm=animations.find(manager.at(255).animation);return result>=0?0:result;
}
API(value) u32 value(u32 n){const auto& s=manager.at(255);const auto* a=manager.th14_bomb_area(s.th14_area_slot);const u32 values[]={
 u32(s.state),s.th14_shot_flags,u32(s.timer.previous),u32(s.timer.current),float_bits(s.timer.fractional),s.timer.flags,
 float_bits(s.movement.position.x),float_bits(s.movement.position.y),float_bits(s.movement.position.z),float_bits(s.movement.speed),float_bits(s.movement.angle),float_bits(s.movement.velocity.x),float_bits(s.movement.velocity.y),float_bits(s.movement.velocity.z),u32(s.damage),float_bits(s.spec->hitbox.x),float_bits(s.spec->hitbox.y),
 vm->flags,vm->flags2,float_bits(vm->rotation.z),float_bits(vm->position.x),float_bits(vm->position.y),float_bits(vm->position.z),vm->layer,
 a->flags,float_bits(a->angle),float_bits(a->size.x),float_bits(a->size.y),float_bits(a->position.x),float_bits(a->position.y),float_bits(a->position.z),u32(a->timer.previous),u32(a->timer.current),float_bits(a->timer.fractional),u32(a->period),u32(a->maximum),u32(a->damage),u32(a->callback==1),spec.type==2?u32(manager.player.th14_cached_power):0,spec.type==3?manager.laser_active[spec.option]:0,animations.script_rng.seed,animations.script_rng.calls,animations.visual_rng.seed,animations.visual_rng.calls};return values[n];}
API(created) u32 created(){return anm_creation_count()-creation_start;}
API(script) i32 script(u32 n){return anm_creation_value(creation_start+n,0);}
API(fire) i32 fire(i32 kind,i32 option,i32 cached,i32 focus,i32 power,i32 frame,i32 available){
 if(spawn(0,-3,0,0,0,1,0,1397,40291,.37)!=0)return -1;
 manager.~ShotManager();new(&manager) ShotManager(sht,anm,animations,world);
 if(!available)for(u32 i=0;i<256;++i)if(manager.spawn(spec,0,{-12.25,400.125,3})<0)return -1;
 manager.player.position={-12.25,400.125,3};manager.player.focused=focus;manager.player.power=power;manager.player.power_step=40;manager.player.th14_cached_power=cached;manager.laser_active.fill(0);if(kind==3)manager.laser_active[option]=u32(cached);
 sht.header.max_power_level=4;sht.groups.resize(10);spec.type=i8(kind);spec.option=i8(option);spec.interval=3;spec.delay=1;
 for(auto& g:sht.groups)g.shots.assign(1,spec);creation_start=anm_creation_count();return manager.fire_frame(frame)?1:-manager.last_error;
}
API(gate_value) u32 gate_value(u32 n){const u32 v[]={anm_creation_count()-creation_start,spec.type==2?u32(manager.player.th14_cached_power):0,spec.type==3?manager.laser_active[spec.option]:0};return v[n];}

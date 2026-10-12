#include "../../cpp/game/ShotManager.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static ShtResource sht;static AnmResource anm;static AnmManager animations;
struct World:ShotWorld{}world;
static ShotManager manager(sht,anm,animations,world);static ShotSpec spec;static AnmVm* vm;
static Enemy enemy;
API(tick) i32 tick(i32 kind,u32 flags,i32 age,float rate,i32 present,i32 hint,float x,i32 callback,i32 state){
 animations.clear();animations.rate=rate;anm.scripts.resize(1);anm.scripts[0].bytes={2,0,8,0,0,0,0,0,255,255,0,0,0,0,0,0};
 vm=animations.create(anm,0,7,0);if(!vm)return -1;vm->flags=2;vm->flags2=0x20200|(hint?0x40:0);vm->rotation.z=.37;vm->position={x,80.125,3};vm->script_position={.125,3.25,0};vm->sprite_size={24,40};vm->scale=vm->extra_scale={1,1};
 manager.player={};manager.player.th14_cached_power=3;manager.player.th14_attached_count=2;manager.player.th14_enemy_manager=true;manager.last_error=0;
 enemy={};enemy.state.instance_id=73;enemy.state.current.position={100,200,0};enemy.state.manager_link.value=&enemy;world.enemies=&enemy.state.manager_link;
 for(u32 i=0;i<256;++i)manager.at(i)={};spec={};spec.type=i8(kind);spec.hitbox={24,40};spec.update=ShotUpdate(callback);spec.native_tail[0]=10;
 auto& s=manager.at(0);s.state=state;s.spec=&spec;s.animation=present?vm->id:0;s.timer.set(age,&animations.rate);s.timer.fractional=age+.375f;s.timer.flags=0x81;s.th14_shot_flags=flags;s.damage=19;s.th14_area_slot=0;s.th14_area_flags=0x81;s.movement.position={x,80.125,3};s.movement.speed=8.125;s.movement.angle=-2.37;s.movement.velocity={99,88,1.5};
 auto& a=*manager.th14_bomb_area(0);a={};a.flags=0x81;a.angle=.61;a.size={12,15};a.position={-11,-12,7};a.damage=7;
 return manager.update()?1:-manager.last_error;
}
API(value) u32 value(u32 n){const auto& s=manager.at(0);const auto& a=*manager.th14_bomb_area(0);const u32 values[]={
 u32(s.state),s.th14_shot_flags,u32(s.animation!=0),u32(s.timer.previous),u32(s.timer.current),float_bits(s.timer.fractional),s.timer.flags,float_bits(s.movement.position.x),float_bits(s.movement.position.y),float_bits(s.movement.position.z),float_bits(s.movement.speed),float_bits(s.movement.angle),float_bits(s.movement.velocity.x),float_bits(s.movement.velocity.y),float_bits(s.movement.velocity.z),
 vm->flags,vm->flags2,float_bits(vm->rotation.z),float_bits(vm->position.x),float_bits(vm->position.y),float_bits(vm->position.z),
 a.flags,float_bits(a.angle),float_bits(a.size.x),float_bits(a.size.y),float_bits(a.position.x),float_bits(a.position.y),float_bits(a.position.z),u32(a.damage),u32(manager.player.th14_cached_power),u32(manager.player.th14_attached_count)};return values[n];}

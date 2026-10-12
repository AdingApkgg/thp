#include "../../cpp/game/BombController.hpp"
#include <cstdlib>
#include <vector>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static ShtResource sht;static AnmResource anm;static AnmManager animations;static GameEconomy economy;static std::vector<std::vector<u32>> events;static AnmVm* main_vm=nullptr;static AnmVm* auxiliary_vm=nullptr;
struct World:PlayerFrameWorld,BombWorld {
 i32 count=7;bool dialogue=false;
 bool bomb_sound(i32 id,float,bool positional)override{events.push_back({1,u32(id),u32(positional)});return true;}
 bool bomb_stop_sound(i32)override{return true;}bool bomb_cancel(Vec3,float,u32,bool)override{return false;}
 i32& bomb_count()override{return count;}bool bomb_background_color(u32)override{return true;}bool bomb_refund_power()override{return false;}bool bomb_cancel_beam(Vec3,bool)override{return false;}
 bool th14_bomb_freeze(bool value)override{events.push_back({2,u32(value)});return true;}
 bool th14_bomb_cancel(Vec3 p,float radius,u32 rewards)override{events.push_back({3,float_bits(p.x),float_bits(p.y),float_bits(p.z),float_bits(radius),rewards});return true;}
 bool th14_bomb_dialogue()const override{return dialogue;}
 bool th14_bomb_circle(Vec3 p,float radius,float growth,i32 duration,i32 damage)override{events.push_back({4,float_bits(p.x),float_bits(p.y),float_bits(p.z),float_bits(radius),float_bits(growth),u32(duration),u32(damage)});return true;}
 bool th14_bomb_item(i32 type,Vec3 p,float angle,float speed)override{events.push_back({5,u32(type),float_bits(p.x),float_bits(p.y),float_bits(p.z),float_bits(angle),float_bits(speed)});return true;}
 bool th14_bomb_shake(i32 amplitude,i32 ramp,i32 hold,i32 fall)override{events.push_back({6,u32(amplitude),u32(ramp),u32(hold),u32(fall)});return true;}
 bool th14_bomb_rectangle(Vec3 p,Vec2 size,float angle,i32 duration,i32 damage)override{events.push_back({7,float_bits(p.x),float_bits(p.y),float_bits(p.z),float_bits(size.x),float_bits(size.y),float_bits(angle),u32(duration),u32(damage)});return true;}
 bool th14_bomb_cancel_rectangle(Vec3 p,Vec2 size,float angle,u32 rewards)override{events.push_back({8,float_bits(p.x),float_bits(p.y),float_bits(p.z),float_bits(size.x),float_bits(size.y),float_bits(angle),rewards});return true;}
}world;
static PlayerFrame player(sht,anm,anm,animations,economy,world);static BombController bomb(animations,anm,player,world,7,&anm);static u32 creation_start;
static void reset(){animations.clear();animations.rate=1;anm.scripts.resize(34);for(auto& s:anm.scripts)s.bytes={2,0,8,0,0,0,0,0};bomb.state={};bomb.selection=5;bomb.last_error=0;world.count=7;world.dialogue=false;events.clear();player.motion.state.position={12.25,400,3};player.motion.state.th14_movement_factor=1;player.state={};player.th14_scale={};player.spell={};creation_start=anm_creation_count();main_vm=auxiliary_vm=nullptr;}
API(start) i32 start(u32 flags,i32 time){reset();player.spell={flags,time,12345};return bomb.start();}
API(start_selection) i32 start_selection(i32 selection,u32 flags,i32 time){reset();bomb.selection=selection;player.spell={flags,time,12345};return bomb.start();}
API(tick) i32 tick(i32 time,i32 active,i32 missing,float rate){reset();animations.rate=rate;auto* vm=animations.create(anm,21,7,0);bomb.state.animation=vm->id;if(missing)animations.clear();bomb.state.active=active;bomb.state.position={12.25,400,3};bomb.state.elapsed.set(time,&animations.rate);events.clear();return bomb.update();}
API(tick_selection) i32 tick_selection(i32 selection,i32 time,i32 active,i32 missing,float rate,i32 dialogue,i32 advanced){
 reset();bomb.selection=selection;animations.rate=rate;world.dialogue=dialogue;
 main_vm=animations.create(anm,28,7,0);main_vm->scale.x=1.75f;bomb.state.animation=main_vm->id;
 auxiliary_vm=animations.create(anm,33,7,0);bomb.state.auxiliary=auxiliary_vm->id;if(missing)animations.destroy(*main_vm);
 bomb.state.active=active;bomb.state.position={12.25,400,3};bomb.state.elapsed.set(time,&animations.rate);bomb.state.elapsed.previous=time-advanced;events.clear();return bomb.update();
}
API(tick_value) u32 tick_value(u32 n){const u32 a[]={u32(bomb.state.active),bomb.state.animation,u32(bomb.state.elapsed.current),float_bits(bomb.state.elapsed.fractional),float_bits(bomb.state.position.x),float_bits(bomb.state.position.y),float_bits(bomb.state.position.z),float_bits(bomb.state.growth),u32(main_vm?main_vm->pending_interrupt:0),u32(auxiliary_vm?auxiliary_vm->pending_interrupt:0)};return a[n];}
API(value) u32 value(u32 n){const u32 a[]={player.spell.flags,u32(player.spell.bonus),u32(world.count),u32(player.state.invincibility.current),float_bits(bomb.state.growth),u32(bomb.state.active),bomb.state.animation,u32(bomb.state.elapsed.current),float_bits(bomb.state.elapsed.fractional)};return a[n];}
API(player_flags) u32 player_flags(){return player.th14_scale.flags;}
API(tick_marisa_a) i32 tick_marisa_a(i32 time,i32 active,i32 missing,float rate,i32 advanced,float dx){
 reset();bomb.selection=2;animations.rate=rate;player.motion.state.position={14.25,300,4};player.motion.state.delta.x=dx;player.motion.state.th14_movement_factor=.75f;player.state.invincibility.set(10,&animations.rate);player.th14_scale.flags=0x24;
 main_vm=animations.create(anm,19,7,0);main_vm->scale.x=1.75f;bomb.state.animation=main_vm->id;
 auxiliary_vm=animations.create(anm,27,7,0);bomb.state.auxiliary=auxiliary_vm->id;if(missing)bomb.state.animation=0xfffffff0u;
 bomb.state.active=active;bomb.state.position={12.25,400,3};bomb.state.growth=-1.5707963705062866f;bomb.state.elapsed.set(time,&animations.rate);bomb.state.elapsed.previous=time-advanced;events.clear();return bomb.update();
}
API(marisa_a_value) u32 marisa_a_value(u32 n){const u32 a[]={u32(bomb.state.active),bomb.state.animation,u32(bomb.state.elapsed.current),float_bits(bomb.state.elapsed.fractional),float_bits(bomb.state.position.x),float_bits(bomb.state.position.y),float_bits(bomb.state.position.z),float_bits(bomb.state.growth),u32(main_vm?main_vm->pending_interrupt:0),u32(auxiliary_vm?auxiliary_vm->pending_interrupt:0),float_bits(main_vm?main_vm->rotation.z:0),u32(player.state.invincibility.current),player.th14_scale.flags,float_bits(player.motion.state.th14_movement_factor)};return a[n];}
API(allocate) void* allocate(u32 size){return std::malloc(size);}
API(marisa_a_child) i32 marisa_a_child(const u32* words,u32 count,u32 spell){
 tick_marisa_a(1,1,0,1,0,0);player.spell.flags=spell;bomb.state.elapsed.set(1,&animations.rate);
 AnmVm* parent=nullptr;for(u32 j=0;j<count;++j){const auto* p=words+j*12;auto* a=animations.create(anm,j+1==count?26:0,7,0,false,false,nullptr,nullptr,j+1==count?main_vm:nullptr);if(!a)return -2;
  a->flags2=p[0];a->rotation.z=float_bits(p[1]);a->position={float_bits(p[2]),float_bits(p[3]),float_bits(p[4])};a->script_position={float_bits(p[5]),float_bits(p[6]),float_bits(p[7])};a->child_position={float_bits(p[8]),float_bits(p[9]),float_bits(p[10])};a->scale={1.25f,2.5f};a->parent=parent;parent=a;
  if(j+1==count){main_vm->child.next=&a->child;a->child.previous=&main_vm->child;}
 }
 events.clear();return bomb.update();
}
API(tick_sakuya_a) i32 tick_sakuya_a(i32 time,i32 active,i32 mode,i32 life,i32 missing_main,i32 missing_aux,i32 aux_age,i32 dialogue,i32 spell,float rate){
 reset();bomb.selection=4;animations.rate=rate;world.dialogue=dialogue;player.spell.flags=spell;
 player.motion.state.position={14.25,300,4};player.motion.state.th14_movement_factor=.75f;player.state.life_state=life;player.state.state_timer.set(9,&animations.rate);player.state.invincibility.set(10,&animations.rate);player.th14_scale.flags=0x28;
 main_vm=animations.create(anm,16,7,0);main_vm->scale.x=1.75f;bomb.state.animation=main_vm->id;
 auxiliary_vm=animations.create(anm,19,7,0);auxiliary_vm->scale.x=2.5f;auxiliary_vm->age.set(aux_age,&animations.rate);bomb.state.auxiliary=auxiliary_vm->id;
 if(missing_main)bomb.state.animation=0xfffffff0u;if(missing_aux)bomb.state.auxiliary=0xfffffff1u;
 bomb.state.active=active;bomb.state.th14_mode=mode;bomb.state.position={12.25,400,3};bomb.state.elapsed.set(time,&animations.rate);events.clear();return bomb.update();
}
API(sakuya_a_value) u32 sakuya_a_value(u32 n){const auto* a=animations.find(bomb.state.auxiliary);const u32 v[]={u32(bomb.state.active),u32(bomb.state.th14_mode),u32(bomb.state.elapsed.current),float_bits(bomb.state.elapsed.fractional),float_bits(bomb.state.position.x),float_bits(bomb.state.position.y),float_bits(bomb.state.position.z),player.th14_scale.flags,u32(player.state.life_state),u32(player.state.state_timer.current),u32(player.state.invincibility.current),float_bits(player.motion.state.th14_movement_factor),float_bits(main_vm?main_vm->scale.x:0),u32(main_vm?main_vm->pending_interrupt:0),u32(a!=nullptr),u32(bomb.state.animation!=0)};return v[n];}
API(event_count) u32 event_count(){return events.size();}API(event_size) u32 event_size(u32 i){return events[i].size();}API(event) u32 event(u32 i,u32 k){return events[i][k];}
API(created) u32 created(){return anm_creation_count()-creation_start;}API(script) i32 script(u32 n){return anm_creation_value(creation_start+n,0);}
API(position) u32 position(u32 n,u32 axis){const auto* vm=animations.find(u32(anm_creation_value(creation_start+n,5)));return vm?float_bits(axis==0?vm->position.x:axis==1?vm->position.y:vm->position.z):0;}

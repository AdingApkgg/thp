#include "../../cpp/game/ShotManager.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static ShotState shot;static ShotPlayer player;static ShotSpec spec;static float rate;
static Enemy enemy;static EnemyLink node;static AnmVm vm,child;static AnmVm::Node child_node;static Th14DamageArea area;
static Th14SakuyaUpdate action;static Th14SakuyaHit hit_action;static u32 inputs[32];
API(input) u32* input(){return inputs;}
static float number(u32 bits){float v;std::memcpy(&v,&bits,4);return v;}
static EnemyLink* configure(){
 shot={};player={};spec={};enemy={};vm={};child={};area={};
 shot.spec=&spec;shot.state=1;shot.animation=77;shot.th14_area_slot=0;rate=number(inputs[17]);
 shot.timer.current=i32(inputs[1]);shot.movement.position={12.25f,300.5f,3.f};shot.movement.angle=-1.5707963705062866f;shot.movement.speed=8;
 shot.th14_shot_flags=(inputs[20]&~0x3cu)|(inputs[0]<<2);shot.th14_area_flags=1;
 spec.native_tail[0]=inputs[2];spec.native_tail[1]=inputs[5];spec.native_tail[3]=inputs[7];spec.native_tail[5]=float_bits(.05f);
 player.th14_cached_power=i32(inputs[3]);player.th14_attached_count=i32(inputs[4]);player.th14_enemy_manager=inputs[9];player.state=i32(inputs[11]);player.th14_dialogue_blocked=inputs[12];player.power=i32(inputs[19])*40;player.power_step=40;
 enemy.state.instance_id=19;enemy.state.current.position={32.25f,180.5f,2.f};enemy.state.th14_attached_knives=i32(inputs[13]);
 node={&enemy,nullptr,nullptr};if(inputs[8])shot.target=&enemy;shot.th14_target_id=inputs[8]?19:0;shot.th14_attachment_offset={-20,120,1};
 shot.th14_steering={-1,0,0,&rate,inputs[18]};shot.th14_decay={i32(inputs[6])-1,i32(inputs[6]),float(inputs[6]),&rate,inputs[18]};
 area.flags=1;area.radius=9;area.growth=2;area.damage=19;shot.damage=19;vm.id=77;vm.flags=7;vm.scale={number(inputs[16]),number(inputs[16])};vm.child.value=&vm;
 child.script_index=14;child.scale={number(inputs[15]),number(inputs[15])};child_node={&child,nullptr,&vm.child};if(inputs[14])vm.child.next=&child_node;
 return inputs[8]==1?&node:nullptr;
}
API(update) i32 update(){auto* enemies=configure();return shot_th14_sakuya_update(shot,player,area,inputs[21]?&vm:nullptr,enemies,inputs[10],&rate,action);}
API(update_value) u32 update_value(u32 n){const u32 values[]={shot.th14_shot_flags,float_bits(shot.movement.speed),float_bits(shot.movement.angle),float_bits(shot.movement.position.x),float_bits(shot.movement.position.y),float_bits(shot.movement.position.z),bool(shot.target),shot.th14_target_id,
 u32(shot.th14_steering.previous),u32(shot.th14_steering.current),float_bits(shot.th14_steering.fractional),shot.th14_steering.flags,u32(shot.th14_decay.previous),u32(shot.th14_decay.current),float_bits(shot.th14_decay.fractional),shot.th14_decay.flags,
 u32(player.th14_cached_power),u32(player.th14_attached_count),u32(shot.damage),area.flags,float_bits(area.radius),float_bits(area.growth),vm.flags,float_bits(vm.scale.x),u32(enemy.state.th14_attached_knives),u32(shot.state),shot.animation};return values[n];}
API(action_value) u32 action_value(u32 n){const u32 values[]={u32(action.interrupt),u32(action.level),u32(action.sound),action.explode,action.retired,bool(action.release),float_bits(action.slowdown)};return values[n];}
API(hit) i32 hit(){auto* enemies=configure();shot.timer.previous=shot.timer.current-i32(inputs[27]);area.argument=inputs[8]?19:0;area.size.y=number(inputs[26]);
 const Vec3 target{shot.movement.position.x+number(inputs[23]),shot.movement.position.y+number(inputs[24]),0};const Vec2 size{24,40};
 return shot_th14_sakuya_hit(shot,player,area,target,inputs[22]?&size:nullptr,number(inputs[25]),enemies,hit_action);
}
API(hit_value) u32 hit_value(u32 n){const u32 values[]={shot.th14_shot_flags,float_bits(shot.movement.speed),float_bits(shot.movement.position.x),float_bits(shot.movement.position.y),float_bits(shot.movement.position.z),u32(player.th14_attached_count),area.flags,bool(shot.target),shot.th14_target_id,float_bits(shot.th14_attachment_offset.x),float_bits(shot.th14_attachment_offset.y),float_bits(shot.th14_attachment_offset.z),u32(enemy.state.th14_attached_knives),player.th14_focused_hits,u32(hit_action.damage)};return values[n];}
API(hit_action_value) u32 hit_action_value(u32 n){const u32 values[]={u32(hit_action.interrupt),u32(hit_action.sound),bool(hit_action.attachment),float_bits(hit_action.slowdown)};return values[n];}
API(slowdown) u32 slowdown(u32 flags,float initial,float delta,u32 spell_flags,i32 spell_id){enemy={};enemy.state.flags=flags;enemy.state.th14_knife_slowdown=initial;shot_th14_sakuya_slowdown(enemy.state,delta,spell_flags,spell_id);return float_bits(enemy.state.th14_knife_slowdown);}
API(clock_rate) u32 clock_rate(float rate,float slowdown){return float_bits(enemy_th14_knife_rate(rate,slowdown));}
API(spawn) i32 spawn(i32 count,i32 limit,u32 flags,u32 timer_flags,float speed){
 shot={};player={};spec={};rate=speed;shot.spec=&spec;player.th14_cached_power=count;spec.native_tail[1]=u32(limit);shot.th14_shot_flags=flags;
 shot.target=reinterpret_cast<Enemy*>(123);shot.th14_target_id=456;
 for(auto* t:{&shot.th14_steering,&shot.th14_decay}){t->previous=18;t->current=19;t->fractional=19.5f;t->rate=&rate;t->flags=timer_flags;}
 return shot_th14_sakuya_spawn(shot,player,&rate)==0;
}
API(value) u32 value(u32 n){const u32 values[]={u32(player.th14_cached_power),shot.th14_shot_flags,u32(shot.target),shot.th14_target_id,
 u32(shot.th14_steering.previous),u32(shot.th14_steering.current),float_bits(shot.th14_steering.fractional),shot.th14_steering.flags,
 u32(shot.th14_decay.previous),u32(shot.th14_decay.current),float_bits(shot.th14_decay.fractional),shot.th14_decay.flags};return values[n];}

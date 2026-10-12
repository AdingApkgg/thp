#include "../../cpp/game/ShotManager.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static ShotState s;static ShotSpec spec;static Enemy enemy,second;
API(tick) i32 tick(i32 state,i32 present,i32 listed,u32 target,u32 flags,i32 age,float angle,float speed,float x,float y,u32 other){
 s={};enemy={};second={};s.state=state;s.timer.current=age;s.movement.position={0,100,3};s.movement.angle=angle;s.movement.speed=speed;s.target=target?&enemy:nullptr;const u32 ids[]={17,73,999,99};s.th14_target_id=ids[target];
 enemy.state.instance_id=73;enemy.state.flags=flags;enemy.state.current.position={x,y,0};enemy.state.manager_link.value=&enemy;enemy.state.manager_link.next=other?&second.state.manager_link:nullptr;
 second.state.instance_id=99;second.state.current.position={other==1?x:-x,y,0};second.state.manager_link.value=&second;
 shot_th14_homing_update(s,present,listed?&enemy.state.manager_link:nullptr);return 1;
}
API(value) u32 value(u32 n){const u32 v[]={s.target==&enemy?1u:s.target==&second?2u:0u,s.th14_target_id,float_bits(s.movement.speed),float_bits(s.movement.angle)};return v[n];}
API(retired) i32 retired(i32 age,float angle,float speed,float x,float y){
 s={};enemy={};second={};spec={};spec.update=ShotUpdate(1);s.spec=&spec;s.state=1;
 s.timer.current=age;s.movement.position={0,100,3};s.movement.angle=angle;s.movement.speed=speed;s.target=&enemy;s.th14_target_id=73;
 enemy.state.instance_id=73;second.state.instance_id=99;second.state.current.position={x,y,0};second.state.manager_link.value=&second;
 static ShtResource resource;static AnmResource anm;static AnmManager animations;static ShotWorld world;
 static ShotManager manager(resource,anm,animations,world);manager.at(0)=s;manager.invalidate_target(&enemy);s=manager.at(0);
 shot_th14_homing_update(s,true,&second.state.manager_link);return 1;
}
API(turn) i32 turn(i32 age,i32 delay,i32 state,float angle){s={};spec={};s.spec=&spec;s.timer.current=age;s.state=state;s.movement.speed=8.125;s.movement.angle=angle;spec.native_tail[0]=u32(delay);shot_th14_delayed_turn(s);return 1;}
API(turn_value) u32 turn_value(u32 n){const u32 v[]={u32(s.state),float_bits(s.movement.speed),float_bits(s.movement.angle)};return v[n];}

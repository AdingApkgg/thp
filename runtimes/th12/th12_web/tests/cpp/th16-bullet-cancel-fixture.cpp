#include "../../cpp/game/BulletTh16.hpp"
#include "../../cpp/game/EclContext.hpp"
#include "../../cpp/game/EnemyManager.hpp"
#include "../../cpp/game/BulletManager.hpp"
#include "../../cpp/game/LaserManager.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static BulletState b;static float rate;static u32 events[32],count,reward_count;
struct Services:Th16CancelServices{
 i32 animation(AnmVm& vm)override{events[count++]=0;events[count++]=u32(vm.pending_interrupt);return 0;}
 bool effect(const Vec3& p,i32 id)override{events[count++]=1;events[count++]=u32(id);events[count++]=float_bits(p.x);events[count++]=float_bits(p.y);events[count++]=float_bits(p.z);return true;}
 bool sound(i32 id,float x)override{events[count++]=2;events[count++]=u32(id);events[count++]=float_bits(x);return true;}
 bool reward(Vec3 p,u32 value)override{return bullet_th16_cancel_reward(p,value,reward_count);}
};
API(run_case) i32 run_case(i32 state,u32 flags,float r,float x,float y,float z,i32 effect,u32 rewards){
 b={};b.state=i16(state);b.flags=flags;b.position={x,y,z};b.velocity={1.25f,-.75f,.5f};b.cancel_effect=effect;
 rate=r;b.lifetime.previous=19;b.lifetime.current=20;b.lifetime.fractional=20.5f;b.lifetime.flags=1;b.lifetime.rate=&rate;count=0;reward_count=0xffffffff;Services services;return bullet_th16_cancel(b,&rate,services,rewards);
}
API(value) u32 value(u32 n){const u32 v[]={b.flags,float_bits(b.position.x),float_bits(b.position.y),float_bits(b.position.z),u32(b.lifetime.previous),u32(b.lifetime.current),float_bits(b.lifetime.fractional),u32(b.vm.pending_interrupt),u32(b.state),reward_count};return v[n];}
API(event_count) u32 event_count(){return count;}
API(event) u32 event(u32 n){return events[n];}
API(circle) i32 circle(i32 state,i32 delay,i32 delayed,u32 hitbox,u32 radius,u32 x,u32 y){b={};b.state=i16(state);b.collision_delay=delay;b.hitbox.x=float_bits(hitbox);b.position={float_bits(x),float_bits(y),0};return bullet_th16_circle_match(b,{0,0,0},float_bits(radius),delayed!=0);}
struct RouteWorld:BulletWorld,LaserWorld{bool sound(i32,float,bool)override{return true;}};
static AnmEnvironment route_anm;static AnmResource route_resource;static RouteWorld route_world;
static BulletManager route_bullets(route_resource,route_anm,route_world,7);
static LaserManager route_lasers(route_resource,route_anm,route_world,7);
static EnemyState route_enemy;static EnemyEnvironment route_env;static EnemyCommandEnvironment route_commands;
static i32 route_state;
API(route_circle) i32 route_circle(i32 state,i32 delay,u32 hitbox,u32 radius,u32 x,u32 y,u32 op){
 if(route_resource.scripts.empty()){
  route_resource.scripts.resize(400);const AnmInstruction data[]={{2,8,100,0},{-1,8,0,0}};
  for(auto& s:route_resource.scripts)s.bytes.assign(reinterpret_cast<const u8*>(data),reinterpret_cast<const u8*>(data)+sizeof data);
 }
 route_bullets.reset();Th16BulletEmitter emitter{};emitter.count=emitter.layers=1;emitter.aim=1;emitter.position={20,20,0};
 const i32 spawned=route_bullets.spawn_th16(emitter,0,0,0);if(spawned)return -100+spawned;
 auto& bullet=route_bullets.at(1999);bullet.state=i16(state);bullet.collision_delay=delay;bullet.hitbox.x=float_bits(hitbox);bullet.position={float_bits(x),float_bits(y),0};bullet.velocity={};bullet.cancel_effect=-1;bullet.flags&=~0x200u;
 route_enemy={};route_commands={};route_commands.bullets=&route_bullets;route_commands.lasers=&route_lasers;
 alignas(4) u8 bytes[20]{};auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=u16(op);cmd->length=20;std::memcpy(bytes+16,&radius,4);
 EclContext context;context.instruction=cmd;EnemyScriptServices services(route_enemy,route_env,route_commands);const i32 result=services.command(context);route_state=bullet.state;return result;
}
API(route_state_value) i32 route_state_value(){return route_state;}
API(route_reward_count) u32 route_reward_count(){return route_bullets.th16_reward_count;}
API(route_empty) i32 route_empty(u32 op){
 route_bullets.reset();route_commands={};route_commands.bullets=&route_bullets;route_commands.lasers=&route_lasers;alignas(4) u8 bytes[20]{};auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=u16(op);cmd->length=20;EclContext context;context.instruction=cmd;EnemyScriptServices services(route_enemy,route_env,route_commands);return services.command(context);
}

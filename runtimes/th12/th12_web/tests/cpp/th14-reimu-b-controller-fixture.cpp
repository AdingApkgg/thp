#include "../../cpp/game/BombController.hpp"
#include <cstdlib>
#include <vector>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static ShtResource sht;static AnmResource anm;static AnmManager animations;static GameEconomy economy;static std::vector<std::vector<u32>> events;
struct World:PlayerFrameWorld,BombWorld {
 i32 count=7;
 bool bomb_sound(i32 id,float x,bool positional)override{events.push_back({1,u32(id),u32(positional),positional?float_bits(x):0});return true;}
 bool bomb_stop_sound(i32)override{return true;}bool bomb_cancel(Vec3,float,u32,bool)override{return false;}
 i32& bomb_count()override{return count;}bool bomb_background_color(u32)override{return true;}bool bomb_refund_power()override{return false;}bool bomb_cancel_beam(Vec3,bool)override{return false;}
 bool th14_bomb_cancel(Vec3 p,float radius,u32 reward)override{events.push_back({2,float_bits(p.x),float_bits(p.y),float_bits(p.z),float_bits(radius),reward});return true;}
 bool th14_bomb_circle(Vec3 p,float r,float g,i32 d,i32 damage)override{events.push_back({3,float_bits(p.x),float_bits(p.y),float_bits(p.z),float_bits(r),float_bits(g),u32(d),u32(damage)});return true;}
 bool th14_bomb_shake_short(i32 d,i32 f,i32 t)override{events.push_back({4,u32(d),u32(f),u32(t)});return true;}
}world;
static PlayerFrame player(sht,anm,anm,animations,economy,world);static BombController bomb(animations,anm,player,world,7,&anm);static u32 creation_start;static AnmVm* aux;static AnmVm* orbs[8];
static void reset(){
 animations.clear();animations.rate=1;anm.scripts.resize(25);for(auto& s:anm.scripts)s.bytes={2,0,8,0,0,0,0,0,255,255,0,0,0,0,0,0};
 bomb.state={};bomb.selection=1;bomb.last_error=0;bomb.th14_orbs={};bomb.th14_orbs_allocated=true;world.count=7;events.clear();player.motion.state.position={12.25,400,3};player.state={};player.state.invincibility.set(10,&animations.rate);player.spell={};
 for(u32 i=0;i<256;++i)*player.shots.th14_bomb_area(i)={};creation_start=anm_creation_count();aux=nullptr;for(auto& o:orbs)o=nullptr;
}
API(start) i32 start(u32 flags,i32 time){reset();player.spell={flags,time,12345};return bomb.start();}
API(start_value) u32 start_value(u32 n){const u32 v[]={player.spell.flags,u32(player.spell.bonus),u32(world.count),u32(player.state.invincibility.current)};return v[n];}
API(tick) i32 tick(i32 time,i32 active,float rate,u32 spell,i32 total){
 reset();animations.rate=rate;player.spell.flags=spell;bomb.state.active=active;bomb.state.position={12.25,400,3};bomb.state.elapsed.set(time,&animations.rate);
 aux=animations.create(anm,24,7,0);bomb.state.auxiliary=aux->id;
 if(time)for(u32 i=0;i<8;++i){auto& o=bomb.th14_orbs[i];o.index=i;o.active=true;o.position={float(10+i),float(100+i),3};o.anchor={12.25,400,3};o.last_delta={1.25,-2.5,0};o.speed=4;o.angle=-1.25f;o.radius=100;o.turn=.04908738657832146f;o.flags=time<=i32((i+9)*10)?2:0;o.timer.set(time,&animations.rate);
  orbs[i]=animations.create(anm,16,7,0);o.animation=orbs[i]->id;player.shots.th14_bomb_orb_area(o.position,o.area);auto* a=player.shots.th14_bomb_area(o.area);a->total=i==3?total:0;
 }
 creation_start=anm_creation_count();events.clear();const bool result=bomb.update();if(time==0)for(u32 i=0;i<8;++i)orbs[i]=animations.find(bomb.th14_orbs[i].animation);return result;
}
API(value) u32 value(u32 n){const u32 v[]={u32(bomb.state.active),u32(bomb.state.elapsed.current),float_bits(bomb.state.elapsed.fractional),u32(player.state.invincibility.current),u32(aux?aux->pending_interrupt:0),u32(bomb.th14_orbs_allocated)};return v[n];}
API(orb_value) u32 orb_value(u32 i,u32 n){const auto& o=bomb.th14_orbs[i];const auto* a=player.shots.th14_bomb_area(o.area);const u32 v[]={float_bits(o.position.x),float_bits(o.position.y),float_bits(o.position.z),float_bits(o.anchor.x),float_bits(o.anchor.y),float_bits(o.anchor.z),float_bits(o.last_delta.x),float_bits(o.last_delta.y),float_bits(o.last_delta.z),float_bits(o.speed),float_bits(o.angle),float_bits(o.radius),float_bits(o.turn),o.flags,u32(o.timer.previous),u32(o.timer.current),float_bits(o.timer.fractional),u32(o.active),u32(o.animation!=0),u32(a!=nullptr),a?a->flags:0,u32(a?a->damage:0),u32(a?a->total:0),u32(a?a->maximum:0),u32(a?a->period:0),a?float_bits(a->position.x):0,a?float_bits(a->position.y):0,a?float_bits(a->position.z):0,u32(orbs[i]?orbs[i]->pending_interrupt:0)};return v[n];}
API(event_count) u32 event_count(){return events.size();}API(event_size) u32 event_size(u32 i){return events[i].size();}API(event) u32 event(u32 i,u32 k){return events[i][k];}
API(created) u32 created(){return anm_creation_count()-creation_start;}API(script) i32 script(u32 n){return anm_creation_value(creation_start+n,0);}
API(position) u32 position(u32 n,u32 axis){const auto* a=animations.find(u32(anm_creation_value(creation_start+n,5)));return a?float_bits(axis==0?a->position.x:axis==1?a->position.y:a->position.z):0;}

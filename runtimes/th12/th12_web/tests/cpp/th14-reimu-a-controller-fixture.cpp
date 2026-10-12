#include "../../cpp/game/BombController.hpp"
#include <vector>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static ShtResource sht;static AnmResource anm;static AnmManager animations;static GameEconomy economy;static std::vector<std::vector<u32>> events;
struct World:PlayerFrameWorld,BombWorld {
 i32 count=7;
 bool bomb_sound(i32 id,float x,bool positional)override{events.push_back({1,u32(id),u32(positional),positional?float_bits(x):0});return true;}
 bool bomb_stop_sound(i32)override{return true;}bool bomb_cancel(Vec3,float,u32,bool)override{return false;}
 i32& bomb_count()override{return count;}bool bomb_background_color(u32)override{return true;}bool bomb_refund_power()override{return false;}bool bomb_cancel_beam(Vec3,bool)override{return false;}
 bool th14_bomb_cancel_rectangle(Vec3 p,Vec2 s,float a,u32 r)override{events.push_back({2,float_bits(p.x),float_bits(p.y),float_bits(p.z),float_bits(s.x),float_bits(s.y),float_bits(a),r});return true;}
 bool th14_bomb_shake_short(i32 d,i32 f,i32 t)override{events.push_back({3,u32(d),u32(f),u32(t)});return true;}
 bool th14_reimu_bomb_hit_effect(Vec3 p,float a)override{events.push_back({4,58,float_bits(p.x),float_bits(p.y),float_bits(p.z),float_bits(a)});return true;}
}world;
static PlayerFrame player(sht,anm,anm,animations,economy,world);static BombController bomb(animations,anm,player,world,7,&anm);
static u32 creation_start;static AnmVm *root,*part,*last,*aux;
static void reset(float rate){
 animations.clear();animations.rate=rate;anm.scripts.resize(25);for(auto& s:anm.scripts)s.bytes={2,0,8,0,0,0,0,0,255,255,0,0,0,0,0,0};
 bomb.state={};bomb.selection=0;bomb.last_error=0;bomb.th14_reimu_areas.fill(256);bomb.th14_reimu_positions={};bomb.th14_reimu_angles={};bomb.th14_reimu_shift={};bomb.th14_reimu_allocated=true;
 world.count=7;events.clear();player.motion.state.position={12.25,400,3};player.motion.state.th14_bomb_shift={};player.state={};player.state.invincibility.set(10,&animations.rate);player.spell={};player.th14_scale.flags=0;
 for(u32 i=0;i<256;++i)*player.shots.th14_bomb_area(i)={};creation_start=anm_creation_count();root=part=last=aux=nullptr;
}
API(start) i32 start(u32 flags,i32 time,float rate){reset(rate);player.spell={flags,time,12345};return bomb.start();}
API(start_value) u32 start_value(u32 n){const u32 v[]={player.spell.flags,u32(player.spell.bonus),u32(world.count),u32(player.state.invincibility.current),player.th14_scale.flags};return v[n];}
API(tick) i32 tick(i32 time,i32 active,float rate,i32 kind,float angle,i32 advanced){
 reset(rate);bomb.state.active=active;bomb.state.position={12.25,400,3};bomb.state.elapsed.set(time,&animations.rate);bomb.state.elapsed.previous=time-advanced;
 player.th14_scale.flags=0x24;player.motion.state.th14_movement_factor=.75;player.motion.state.th14_bomb_shift={2,3,4};
 aux=animations.create(anm,24,7,0);bomb.state.auxiliary=aux->id;bomb.state.animation=999999;
 if(kind){root=animations.create(anm,14,7,0);part=animations.create(anm,13,7,0);root->flags2=part->flags2=0;root->child.next=&part->child;part->child.previous=&root->child;
  bomb.state.animation=root->id;part->rotation.z=angle;part->scale.x=kind==2?-1:1;
  if(kind==3){last=animations.create(anm,13,7,0);last->flags2=0;last->rotation.z=1.5;last->scale.x=1;part->script_index=-2;part->child.next=&last->child;last->child.previous=&part->child;}
 }
 constexpr i32 damages[]={300,100,70,50};constexpr float heights[]={96,80,64,40};
 for(u32 i=0;i<4;++i){player.shots.th14_reimu_bomb_area({12.25,400,3},{128,heights[i]},300,bomb.th14_reimu_areas[i]);player.shots.th14_bomb_area(bomb.th14_reimu_areas[i])->damage=damages[i];}
 for(u32 i=0;i<10;++i){bomb.th14_reimu_positions[i]={float(10+i),float(100+i),3};bomb.th14_reimu_angles[i]=float(.1*double(i));}
 auto& v=bomb.th14_reimu_shift;v.start[0]=0;v.end[0]=-12;v.timer.set(3,&animations.rate);v.duration=20;v.mode=InterpolationMode(22);
 creation_start=anm_creation_count();events.clear();return bomb.update();
}
API(value) u32 value(u32 n){const auto& s=player.motion.state;const u32 v[]={u32(bomb.state.active),u32(bomb.state.animation!=0),u32(bomb.state.elapsed.current),float_bits(bomb.state.elapsed.fractional),u32(player.state.invincibility.current),player.th14_scale.flags,float_bits(s.th14_movement_factor),float_bits(s.th14_bomb_shift.x),float_bits(s.th14_bomb_shift.y),float_bits(s.th14_bomb_shift.z),u32(bomb.th14_reimu_allocated),root?root->flags2:0,part?part->flags2:0,last?last->flags2:0,u32(aux?aux->pending_interrupt:0)};return v[n];}
API(area_value) u32 area_value(u32 i,u32 n){const auto* a=player.shots.th14_bomb_area(bomb.th14_reimu_areas[i]);const u32 v[]={a->flags,float_bits(a->angle),float_bits(a->size.x),float_bits(a->size.y),float_bits(a->position.x),float_bits(a->position.y),float_bits(a->position.z),u32(a->timer.previous),u32(a->timer.current),float_bits(a->timer.fractional),u32(a->damage),u32(a->total),u32(a->maximum),u32(a->period),u32(a->callback==2)};return v[n];}
API(history) u32 history(u32 i,u32 n){const auto p=bomb.th14_reimu_positions[i];const u32 v[]={float_bits(p.x),float_bits(p.y),float_bits(p.z),float_bits(bomb.th14_reimu_angles[i])};return v[n];}
API(interpolator) u32 interpolator(u32 n){const auto& v=bomb.th14_reimu_shift;const u32 values[]={float_bits(v.start[0]),float_bits(v.end[0]),u32(v.timer.previous),u32(v.timer.current),float_bits(v.timer.fractional),u32(v.duration),u32(v.mode)};return values[n];}
API(event_count) u32 event_count(){return events.size();}API(event_size) u32 event_size(u32 i){return events[i].size();}API(event) u32 event(u32 i,u32 k){return events[i][k];}
API(created) u32 created(){return anm_creation_count()-creation_start;}API(script) i32 script(u32 n){return anm_creation_value(creation_start+n,0);}
API(position) u32 position(u32 n,u32 axis){const auto* a=animations.find(u32(anm_creation_value(creation_start+n,5)));return a?float_bits(axis==0?a->position.x:axis==1?a->position.y:a->position.z):0;}
static u32 hit_result[5];
API(hit) i32 hit(u32 seed,float px,float py,float pz,float hx,float hy,float hz,i32 damage){
 reset(1);sht.header.native_extra[0]=100000;animations.script_rng={u16(seed),0,0};animations.visual_rng={54321,0,77};u32 slot;
 if(!player.shots.th14_reimu_bomb_area({px,py,pz},{1024,1024},300,slot))return 0;
 auto* a=player.shots.th14_bomb_area(slot);a->damage=damage;a->period=1;events.clear();i32 result=0;
 const bool okay=player.shots.damage_th14({hx,hy,hz},nullptr,4,0,true,economy,result,77,0);
 hit_result[0]=u32(result);hit_result[1]=animations.script_rng.seed;hit_result[2]=animations.script_rng.calls;hit_result[3]=animations.visual_rng.seed;hit_result[4]=animations.visual_rng.calls;return okay;
}
API(hit_value) u32 hit_value(u32 n){return hit_result[n];}
static i32 displacement[2];
API(move) void move(i32 dx,i32 dy,float x,float y,float factor){player_th14_bomb_displacement(dx,dy,{x,y,0},factor);displacement[0]=dx;displacement[1]=dy;}
API(move_value) i32 move_value(u32 n){return displacement[n];}

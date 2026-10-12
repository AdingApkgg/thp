#include "../../cpp/game/ShotManager.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmResource anm;static ShtResource sht;static AnmManager animations;static GameEconomy economy;static ShotSpec spec;static i32 damage=0;
struct World:ShotWorld {i32 sounds=0,last_sound=-1;float last_x=0;bool sound(i32 id,float x)override{++sounds;last_sound=id;last_x=x;return true;}}world;
static ShotManager shots(sht,anm,animations,world);static AnmVm* vm=nullptr;
API(begin) i32 begin(){
 anm.scripts.resize(6);for(auto& s:anm.scripts)s.bytes={2,0,8,0,0,0,0,0,255,255,0,0,0,0,0,0};sht.header.native_extra[0]=220;
 spec.damage=22;spec.hitbox={16,16};spec.animation=0;spec.sound=-1;spec.speed=8;spec.angle=-1.25f;spec.spawn=static_cast<ShotSpawn>(4);spec.update=static_cast<ShotUpdate>(4);spec.extra_callback=4;spec.native_tail[0]=17;spec.native_tail[1]=31;
 if(shots.spawn(spec,0,{12.25,301.125,.1f})<0)return 0;shots.at(0).damage=19;vm=animations.find(shots.at(0).animation);return vm!=nullptr;
}
API(hit) i32 hit(){const Vec2 size{16,16};return shots.damage_th14(shots.at(0).movement.position,&size,0,0,true,economy,damage);}
API(tick) void tick(){shots.update_th14_areas();}
API(other_counter) u32 other_counter(){return shots.player.th14_plain_hits;}
API(value) u32 value(u32 n){const auto& s=shots.at(0);const auto* a=shots.th14_bomb_area(1);const u32 v[]={u32(damage),u32(s.state),s.th14_area_flags,s.th14_area_slot,u32(vm?vm->pending_interrupt:0),u32(world.sounds),u32(world.last_sound),float_bits(world.last_x),shots.player.th14_focused_hits,shots.player.th14_hits_184bc,a->flags,u32(a->damage),u32(a->period),u32(a->timer.current),u32(a->total),u32(a->moving),shots.th14_bomb_area(0)->flags,float_bits(a->radius),float_bits(a->position.x),float_bits(a->position.y),float_bits(s.movement.speed)};return v[n];}

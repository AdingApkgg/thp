#include "../../cpp/game/ShotManager.hpp"
#include <new>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static ShtResource sht;static AnmResource anm;static AnmManager animations;
struct World:ShotWorld{}world;
static ShotManager manager(sht,anm,animations,world);static Enemy target;static i32 damage;
static void reset(){manager.~ShotManager();animations.clear();new(&manager)ShotManager(sht,anm,animations,world);sht.header.native_extra[0]=220;}
API(template_layer) i32 template_layer(u32 layer){
 reset();anm.scripts.resize(6);anm.templates=std::make_shared<AnmTemplatesTh14>();anm.templates->scripts.resize(6);
 for(u32 i=0;i<6;++i){anm.scripts[i].bytes={2,0,8,0,0,0,0,0};auto& vm=anm.templates->scripts[i];vm.initialize();vm.layer=layer;vm.script_index=i;vm.script_begin=vm.instruction=reinterpret_cast<AnmInstruction*>(anm.scripts[i].bytes.data());vm.resource=&anm;}
 ShotSpec spec{};spec.animation=0;spec.sound=-1;spec.damage=7;spec.angle=-1.57f;spec.speed=8;spec.hitbox={4,4};
 const i32 slot=manager.spawn(spec,7,{0,400,0});if(slot<0)return -999;auto* vm=animations.find(manager.at(u32(slot)).animation);return vm?i32(vm->layer):-998;
}
API(last_hit) i32 last_hit(u32 active,i32 advanced,u32 duplicate){
 reset();target.state.death_reference={-77,88};
 for(u32 i=0;i<2;++i){auto& a=*manager.th14_bomb_area(i);a={};a.flags=(active&(1u<<i))?3:0;a.radius=20;a.position=i?Vec3{-10,-12,0}:Vec3{10,12,0};a.timer.previous=0;a.timer.current=1;a.period=1;a.maximum=9999999;a.damage=7;a.stamp=(duplicate&(1u<<i))?14:0;}
 GameEconomy economy;return manager.damage_th14({0,0,0},nullptr,25,0,advanced,economy,damage,0,14,&target);
}
API(hit_value) u32 hit_value(u32 n){if(n==2)return u32(damage);u32 b;const float v=n?target.state.death_reference.y:target.state.death_reference.x;std::memcpy(&b,&v,4);return b;}

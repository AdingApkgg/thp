// Retained native pointer presence is represented by a safe retirement marker.
#include "../../cpp/game/ShotManager.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
namespace {ShotState s;ShotSpec spec;ShotPlayer player;AnmVm vm;Enemy enemy;ShtResource resource;float rate=1;
void setup(i32 power,u32 flags,float x,float y){
    s={};spec={};player={};vm={};enemy={};spec.hitbox.x=40;s.spec=&spec;s.state=1;s.movement.position={0,100,0};s.movement.speed=8;s.movement.angle=-1.25f;s.th14_area_flags=0xa5;
    s.timer.set(0,&rate);s.th14_steering.set(0,&rate);s.th14_decay.set(0,&rate);player.power=power*40;player.power_step=40;vm.flags=7;vm.scale={1,1};enemy.state.instance_id=73;enemy.state.flags=flags;enemy.state.current.position={x,y,0};enemy.state.manager_link.value=&enemy;
    resource.header.max_power_level=4;resource.groups.resize(10);for(u32 j=0;j<10;++j){resource.groups[j].shots.resize(3);resource.groups[j].shots[2].hitbox.x=40+2*j;resource.groups[j].shots[2].damage=i16(20+j);}
}}
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(spawn) u32 spawn(i32 power,u32 flags,float x,float y){rate=1;setup(power,flags,x,y);return shot_th14_focused_spawn(s,player,vm,&enemy.state.manager_link,&rate);}
API(update) i32 update(const u32* p){rate=float_bits(p[4]);setup(i32(p[0]),p[1],float_bits(p[2]),float_bits(p[3]));s.timer.set(i32(p[5]),&rate);s.th14_decay.set(i32(p[6]),&rate);s.th14_steering.set(i32(p[7]),&rate);
    player.focused=p[8];player.th14_shooting_blocked=p[10];player.state=i32(p[11]);s.target=nullptr;s.th14_homing_target_retired=p[12]!=0;s.th14_target_id=p[12]?74:0;player.th14_cached_power=i32(p[13]);player.special_active=p[14];s.th14_saved_speed=8;s.th14_area_radius=40;s.damage=19;
    return shot_th14_focused_update(s,player,vm,&enemy.state.manager_link,resource,p[9],&rate);
}
API(value) u32 value(u32 n){const u32 values[]={u32(s.target==&enemy||s.th14_homing_target_retired),s.th14_target_id,float_bits(s.movement.angle),float_bits(s.th14_saved_speed),s.th14_area_flags,float_bits(s.th14_area_radius),float_bits(s.th14_area_growth),u32(s.th14_decay.previous),u32(s.th14_decay.current),float_bits(s.th14_decay.fractional),float_bits(vm.scale.x),float_bits(vm.scale.y),vm.flags,float_bits(s.movement.speed),u32(s.state),u32(player.th14_cached_power),u32(s.damage),u32(s.th14_steering.previous),u32(s.th14_steering.current),float_bits(s.th14_steering.fractional)};return values[n];}

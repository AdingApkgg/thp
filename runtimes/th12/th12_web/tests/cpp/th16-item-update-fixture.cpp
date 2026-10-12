#include "../../cpp/game/ItemManager.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <vector>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmResource resource;static AnmEnvironment env;
struct World final:ItemWorld {
    std::vector<u32> events;
    bool item_th16_collect(ItemState&)override{events.insert(events.end(),{0,1,10,2});return true;}
    bool sound(i32 id,float x)override{events.insert(events.end(),{3,u32(id),float_bits(x)});return true;}
} world;
static ItemManager manager(resource,env,world,7);
static u32 selected_slot=4695;
API(run_case) i32 run_case(i32 state,i32 clock,float rate,float x,float y,float z,i32 scenario,float speed,i32 kind){
    manager.reset();env.rate=rate;world.events.clear();selected_slot=kind<=8?599:4695;auto& i=manager.at(selected_slot);i.state=state;i.type=i.display_type=kind;i.position={x,y,z};i.velocity={.125f,-.25f,.375f};i.reserved_44c=speed;i.th16_angle=.75f;i.attraction_speed=2.5f;i.lifetime.set(clock,&env.rate);
    auto& p=manager.player;p={};p.state=scenario==1?2:scenario==2?4:1;p.position={0,scenario==3?100.f:400.f,0};p.character=scenario%4;p.bomb_attract=scenario==4;p.season_attract=scenario==5;p.spell_attract=scenario==6;p.focused=scenario==7;
    p.pickup={-2,p.position.y-2,2,p.position.y+2};if(kind!=16)p.pickup={9999,9999,10000,10000};p.focused_attract={-64,p.position.y-64,64,p.position.y+64};p.unfocused_attract={-32,p.position.y-32,32,p.position.y+32};return manager.update();
}
API(value) u32 value(u32 n){auto& i=manager.at(selected_slot);const u32 v[]={float_bits(i.position.x),float_bits(i.position.y),float_bits(i.position.z),float_bits(i.velocity.x),float_bits(i.velocity.y),float_bits(i.velocity.z),float_bits(i.reserved_44c),float_bits(i.th16_angle),u32(i.lifetime.previous),u32(i.lifetime.current),float_bits(i.lifetime.fractional),i.lifetime.flags,u32(i.state),float_bits(i.attraction_speed),u32(i.delay),u32(i.th16_force_attract),i.vm.color,manager.active_count,u32(manager.th16_attract_timer)};return v[n];}
API(event_count) u32 event_count(){return world.events.size();}
API(event) u32 event(u32 n){return world.events[n];}

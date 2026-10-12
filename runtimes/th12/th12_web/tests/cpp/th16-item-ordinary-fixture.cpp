#include "../../cpp/game/ItemManager.hpp"
#include "../../cpp/game/EclContext.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include <vector>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmResource resource;static AnmEnvironment env;
struct World final:ItemWorld {
 std::vector<u32> events;
 bool item_th16_spawn_notice(Vec3 p,i32 type)override{events.insert(events.end(),{0,101,float_bits(p.x),float_bits(p.y),float_bits(p.z),1,u32(type==4||type==5?74:48)});return true;}
} world;
static ItemManager manager(resource,env,world,7);
static void prepare(){resource={};resource.scripts.resize(142);const AnmInstruction code[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};for(auto& s:resource.scripts){s.bytes.resize(sizeof code);std::memcpy(s.bytes.data(),code,sizeof code);}}
API(run_case) i32 run_case(i32 kind,u32 count,i32 drop,float x,float y,float z,i32 full,float angle,float speed,i32 force){
 prepare();manager.reset();if(full)for(u32 n=0;n<600;++n)manager.spawn_ordinary_th16(1,{},0,0);
 std::memset(&manager.at(599),0,sizeof(ItemState));manager.at(599).th16_generation=0x12345678;manager.at(599).th16_angle=.25f;
 // Reconstruct the ordinary head's successor after zeroing the fresh slot.
 if(!full)manager.at(599).th16_free_next=&manager.at(598);
 manager.th16_spawn_count=count;world.th16_drop_counter=drop;world.events.clear();return manager.spawn_ordinary_th16(kind,{x,y,z},angle,speed,force);
}
API(value) u32 value(u32 n){const auto& i=manager.at(599);const u32 words[]={float_bits(i.position.x),float_bits(i.position.y),float_bits(i.position.z),float_bits(i.velocity.x),float_bits(i.velocity.y),float_bits(i.velocity.z),float_bits(i.reserved_44c),float_bits(i.th16_angle),u32(i.lifetime.previous),u32(i.lifetime.current),float_bits(i.lifetime.fractional),i.lifetime.flags,u32(i.state),u32(i.type),u32(i.display_type),u32(i.delay),i.th16_generation,u32(i.th16_force_attract),manager.th16_spawn_count,u32(manager.th16_ordinary_slot()),u32(world.th16_drop_counter),i.vm.color,u32(i.vm.script_index),u32(i.th16_indicator.script_index)};return words[n];}
API(event_count) u32 event_count(){return world.events.size();}
API(event) u32 event(u32 n){return world.events[n];}

API(reset) void reset(){prepare();manager.reset();world.events.clear();}
API(spawn_next) i32 spawn_next(){const auto slot=manager.th16_ordinary_slot();manager.spawn_ordinary_th16(1,{},0,1);return slot;}
API(count) u32 count(){return manager.th16_spawn_count;}
API(recycle) void recycle(u32 slot){manager.release_th16(manager.at(slot));}
API(state) i32 state(u32 slot){return manager.at(slot).state;}
API(free_slot) i32 free_slot(){return manager.th16_ordinary_slot();}

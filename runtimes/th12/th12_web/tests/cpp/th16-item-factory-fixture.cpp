#include "../../cpp/game/ItemManager.hpp"
#include "../../cpp/game/EclContext.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include <cstring>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmResource resource;static AnmEnvironment env;static ItemWorld world;static ItemManager manager(resource,env,world,7);
API(run_case) i32 run_case(i32 kind,u32 count,u32 load,i32 full,float x,float y,float z,float angle,float speed,i32 force){
 manager.reset();manager.th16_spawn_count=count;manager.th16_cancel_count=load;manager.th16_generation=0x12345678;
 if(full)for(u32 n=0;n<4096;++n)manager.spawn_cancel_th16(16,{0,0,0},0,0);
 if(full){manager.th16_spawn_count=count;std::memset(&manager.at(4695),0,sizeof(ItemState));}
 return manager.spawn_cancel_th16(kind,{x,y,z},angle,speed,force);
}
API(value) u32 value(u32 n){const auto& i=manager.at(4695);const u32 words[]={float_bits(i.position.x),float_bits(i.position.y),float_bits(i.position.z),float_bits(i.velocity.x),float_bits(i.velocity.y),float_bits(i.velocity.z),float_bits(i.reserved_44c),float_bits(i.th16_angle),u32(i.lifetime.previous),u32(i.lifetime.current),float_bits(i.lifetime.fractional),i.lifetime.flags,u32(i.state),u32(i.type),u32(i.display_type),u32(i.delay),i.th16_generation,u32(i.th16_force_attract),manager.th16_spawn_count,u32(manager.th16_free_slot())};return words[n];}
API(reset) void reset(){manager.reset();}
API(spawn_next) i32 spawn_next(){const i32 slot=manager.th16_free_slot();if(manager.spawn_cancel_th16(16,{17.25f,61.5f,2},0,1)<0)return -2;return slot;}
API(count) u32 count(){return manager.th16_spawn_count;}
API(recycle) void recycle(u32 n){manager.release_th16(manager.at(n));}
API(state) i32 state(u32 n){return manager.at(n).state;}
API(free_slot) i32 free_slot(){return manager.th16_free_slot();}
API(activate) i32 activate(i32 kind,i32 season,u32 flags){
 resource={};resource.scripts.resize(142);
 const AnmInstruction code[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};
 for(auto& s:resource.scripts){s.bytes.resize(sizeof code);std::memcpy(s.bytes.data(),code,sizeof code);}
 manager.reset();manager.th16_season=season;auto& i=manager.at(4695);i.type=kind;i.state=6;i.th16_indicator.flags=flags;i.th16_indicator.instruction=reinterpret_cast<AnmInstruction*>(17);i.vm.parent=reinterpret_cast<AnmVm*>(17);return manager.activate(i);
}
API(activation_word) u32 activation_word(u32 n){const auto& i=manager.at(4695);const u32 v[]={u32(i.state),u32(i.vm.script_index),i.th16_indicator.flags,i.th16_indicator.instruction?17u:0xffffffffu,i.vm.parent?17u:0u};return v[n];}

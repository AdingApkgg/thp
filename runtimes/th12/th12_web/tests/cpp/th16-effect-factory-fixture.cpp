#include "../../cpp/game/AnmManager.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmResource resource;static AnmManager manager;static AnmVm* vm;
API(run_case) i32 run_case(i32 layer,u32 flags,float rotation,i32 present){
 manager.clear();resource={};resource.scripts.resize(1);const AnmInstruction code[]={{i16(anm_canonical_opcode(0)),8,32760,0},{-1,8,32760,0}};resource.scripts[0].bytes.resize(sizeof code);std::memcpy(resource.scripts[0].bytes.data(),code,sizeof code);
 const Vec3 position{-12.25f,70.5f,.25f};vm=manager.create(resource,0,7,u32(layer),false,false,present?&position:nullptr,nullptr,nullptr,false,&rotation,flags|0x400u);return vm?1:0;
}
API(value) u32 value(u32 n){const u32 v[]={vm->layer,vm->flags2,float_bits(vm->position.x),float_bits(vm->position.y),float_bits(vm->position.z),float_bits(vm->rotation.z)};return v[n];}

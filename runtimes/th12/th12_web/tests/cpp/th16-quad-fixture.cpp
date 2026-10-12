#include "../../cpp/game/AnmGeometry.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static Vec3 out[4];
API(run_case) i32 run_case(u32 mode,u32 resolution,u32 origin,u32 anchor,u32 relation,float rate){
 AnmVm vm{},parent{};for(auto* p:{&vm,&parent}){p->initialize();p->position={127.25f,200.75f,.375f};p->script_position={3.25f,-9.5f,.125f};p->child_position={4.5f,2.25f,.25f};p->rotation={.125f,-.25f,.375f};p->scale={1.1f,-.625f};p->extra_scale={.75f,1.25f};p->sprite_size={31.75f,47.625f};p->pivot={2.3f,-7.1f};}
 parent.scale={.5f,2};parent.extra_scale={3,4};vm.flags|=(anchor%3)<<18|(anchor/3)<<20;vm.flags2=resolution<<20|origin<<18|(relation==4?0x800000:0)|(relation==5?0x10000:0);vm.set_drawing_mode(mode);
 vm.parent=relation==1||relation==3||relation==5?&parent:nullptr;vm.th16_transform_parent=relation>=2?&parent:nullptr;
 return anm_quad_positions(vm,out,{rate,{320,16},{111,23}});
}
API(value) u32 value(u32 n){return float_bits(reinterpret_cast<float*>(out)[n]);}

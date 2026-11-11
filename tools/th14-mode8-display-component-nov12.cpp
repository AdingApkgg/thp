#include "AnmProjection.hpp"
#include <cstring>
using namespace th11;
#define API(n) extern "C" __attribute__((export_name(#n)))
static u32 input[8+2*371],output[33];
static float f(u32 u){float x;std::memcpy(&x,&u,4);return x;}
static void fill(AnmVm& v,const u32* r){
 v={};v.initialize();const u32 flags=r[0x18/4];
 v.flags=(flags&15)|((flags&0x10000)?0x4000:0);v.th13_native_flags=flags;v.flags2=r[0x1c/4];
 v.position={f(r[0x59c/4]),f(r[0x5a0/4]),f(r[0x5a4/4])};
 v.script_position={f(r[0x3c/4]),f(r[0x40/4]),f(r[0x44/4])};
 v.child_position={f(r[0x4ec/4]),f(r[0x4f0/4]),f(r[0x4f4/4])};
 v.pivot={f(r[0x90/4]),f(r[0x94/4])};v.scale={f(r[0x60/4]),f(r[0x64/4])};v.extra_scale={f(r[0x68/4]),f(r[0x6c/4])};
 std::memcpy(v.sprite_matrix.m,r+0x3e0/4,64);std::memcpy(v.transform_matrix.m,r+0x420/4,64);
}
API(input_ptr) u32 input_ptr(){return u32(input);}
API(output_ptr) u32 output_ptr(){return u32(output);}
API(run) u32 run(){
 AnmVm vm{},parent{};fill(vm,input+8);fill(parent,input+8+371);if(input[7])vm.parent=&parent;
#if defined(TH14_MODE8_SPACE_CANDIDATE)
 const AnmRenderSpace space{f(input[2]),{float(i32(input[5])),float(i32(input[6]))},{float(i32(input[3])),float(i32(input[4]))}};
 const auto world=anm_world_matrix_th14(vm,false,space);
#else
 const auto world=anm_world_matrix(vm,false);
#endif
 std::memcpy(output,world.m,64);std::memcpy(output+16,vm.transform_matrix.m,64);output[32]=vm.flags&12;return 33;
}

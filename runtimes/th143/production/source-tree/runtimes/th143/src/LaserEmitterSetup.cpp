#include "LaserEmitterSetup.hpp"
namespace th143 {
i32 laser_emitter_setup(Emitters& state,Vm& vm,VmHost& host){
 const u32 op=vm.instruction->opcode;if(op!=700&&op!=701)return -2;
 const i32 index=vm.integer_argument(0,host);if(index<0||index>=i32(Emitters::count))return -2;
 const u32 base=u32(index)*Emitters::stride;
 if(op==700){static constexpr u32 offsets[]={0x644,0x648,0x64c,0x97c};for(u32 i=0;i<4;++i)state.put(base+offsets[i],word(vm.float_argument(i+1,host)));}
 else for(u32 i=0;i<5;++i)state.put(base+0x98c+i*4,u32(vm.integer_argument(i+1,host)));
 return vm.failed?-2:0;
}
}

#include "EmitterPlacement.hpp"
#include "DirectionVector.hpp"
namespace th143 {
i32 emitter_placement_command(Emitters& s,Vm& vm,VmHost& host){
 const u32 op=vm.instruction->opcode;if(op<626||op>628)return -2;const i32 i=vm.integer_argument(0,host);if(i<0||i>=i32(Emitters::count))return -2;
 const float x=vm.float_argument(1,host);if(op==627)s.put(u32(i)*Emitters::stride+0x660,word(x));
 else{const float y=vm.float_argument(2,host);if(op==626){DirectionVector v;if(!direction_vector(x,y,v))return -2;s.put(0x3e7c+u32(i)*12,word(v.x));s.put(0x3e80+u32(i)*12,word(v.y));}
 else{s.put(0x3f3c+u32(i)*12,word(x));s.put(0x3f40+u32(i)*12,word(y));s.put(0x3f44+u32(i)*12,x<-990.f?0:word(1.f));}}
 return vm.failed?-2:0;
}
}

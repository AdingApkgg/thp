#include "EclPolar.hpp"
#include "DirectionVector.hpp"
namespace th143 {
i32 ecl_polar_command(Vm& vm,VmHost& host){
 if(vm.instruction->opcode!=81)return -2;
 float angle=vm.float_argument(2,host);if(vm.failed)return -2;
 u32 count=0;
 while(angle>real(0x40490fdb)){angle-=real(0x40c90fdb);if(count++>32)break;}
 while(real(0xc0490fdb)>angle){angle+=real(0x40c90fdb);if(count++>32)break;}
 const float speed=vm.float_argument(3,host);if(vm.failed)return -2;
 DirectionVector vector;if(!direction_vector(angle,speed,vector))return -2;
 auto* x=vm.reference(0,host,true);if(vm.failed||!x)return -2;
 const u32 xbits=word(vector.x);std::memcpy(x,&xbits,4);
 auto* y=vm.reference(1,host,true);if(vm.failed||!y)return -2;
 const u32 ybits=word(vector.y);std::memcpy(y,&ybits,4);return 0;
}
}

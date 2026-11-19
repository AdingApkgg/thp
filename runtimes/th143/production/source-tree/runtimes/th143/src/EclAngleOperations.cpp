#include "EclAngleOperations.hpp"
#include <cmath>
namespace th143 {
i32 ecl_angle_operation(Vm& vm,VmHost& host){
 const u16 op=vm.instruction->opcode;float result;
 if(op==82){result=vm.float_argument(0,host);u32 count=0;while(result>real(0x40490fdb)){result-=real(0x40c90fdb);if(count++>32)break;}while(real(0xc0490fdb)>result){result+=real(0x40c90fdb);if(count++>32)break;}}
 else if(op==87){const float x1=vm.float_argument(1,host),y1=vm.float_argument(2,host),x2=vm.float_argument(3,host),y2=vm.float_argument(4,host);const float y=y2-y1,x=x2-x1;result=float(std::atan2(double(y),double(x)));}
 else if(op==89){const float first=vm.float_argument(1,host),second=vm.float_argument(2,host),difference=second-first;if(difference>real(0x40490fdb)){const float adjusted=first+real(0x40c90fdb);result=second-adjusted;}else if(first-second>real(0x40490fdb)){const float adjusted=first-real(0x40c90fdb);result=second-adjusted;}else result=difference;}
 else return -2;
 if(vm.failed)return -2;auto* output=vm.reference(0,host,true);if(vm.failed||!output)return -2;const u32 bits=word(result);std::memcpy(output,&bits,4);return 0;
}
}

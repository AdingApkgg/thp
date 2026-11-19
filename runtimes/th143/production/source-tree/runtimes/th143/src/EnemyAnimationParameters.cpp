#include "EnemyAnimationParameters.hpp"
namespace th143 {
i32 enemy_animation_parameter_command(AnmView actor,Vm& vm,VmHost& host){
 if(vm.instruction->opcode==552){const u32 value=u32(vm.integer_argument(0,host));if(vm.failed)return -2;actor.put(0x31c,value);return 0;}
 if(vm.instruction->opcode!=322)return -2;const u32 value=u32(vm.integer_argument(1,host));const i32 index=vm.integer_argument(0,host);if(vm.failed)return -2;
 const std::int64_t at=0x2a4+std::int64_t(index)*4;if(at<0||at>0x41b4)return -2;actor.put(u32(at),value);return 0;
}
}

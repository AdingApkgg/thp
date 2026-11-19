#include "EnemySpecialFlag.hpp"
namespace th143 {
i32 enemy_special_flag_command(Emitters& state,Vm& vm,VmHost& host){
 if(vm.instruction->opcode!=568)return -2;const u32 value=u32(vm.integer_argument(0,host));if(vm.failed)return -2;
 state.put(0x4030,(state.get(0x4030)&~1u)|(value&1u));return 0;
}
}

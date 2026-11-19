#include "EnemyTimeScale.hpp"
namespace th143 {
i32 enemy_time_scale_command(Emitters& state,Vm& vm,VmHost& host,u32& rate){
 if(vm.instruction->opcode!=547)return -2;
 const float value=vm.float_argument(0,host);if(vm.failed)return -2;
 state.put(0x388,word(value));rate=word(value);return 0;
}
}

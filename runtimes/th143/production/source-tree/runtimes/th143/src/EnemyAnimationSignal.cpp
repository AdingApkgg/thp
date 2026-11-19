#include "EnemyAnimationSignal.hpp"
namespace th143 {
i32 enemy_animation_signal_command(AnmView v,Vm& vm,VmHost& host,EnemyAnimationSignalHost& services){
 if(!v.data||!vm.instruction||vm.instruction->opcode!=317)return -2;
 const i32 slot=vm.integer_argument(0,host),signal=vm.integer_argument(1,host);if(vm.failed||slot<0||slot>=24)return -2;
 return services.enemy_animation_signal(v.get(0x124+u32(slot)*4),i32(std::int16_t(u16(u32(signal)))))?0:-2;
}
}

#include "EnemyFlag27.hpp"
namespace th143 {
i32 enemy_flag27_command(Emitters& actor,Vm& vm,VmHost& host){if(vm.instruction->opcode!=544)return -2;const u32 value=u32(vm.integer_argument(0,host));if(vm.failed)return -2;actor.put(0x4100,(actor.get(0x4100)&~0x08000000u)|((value&1u)<<27));return 0;}
}

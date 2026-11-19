#include "EnemyHitSound.hpp"
namespace th143 {
i32 enemy_hit_sound_command(Emitters& actor,Vm& vm,VmHost& host){if(vm.instruction->opcode!=553)return -2;const u32 id=u32(vm.integer_argument(0,host));if(vm.failed)return -2;actor.put(0x4094,id);return 0;}
}

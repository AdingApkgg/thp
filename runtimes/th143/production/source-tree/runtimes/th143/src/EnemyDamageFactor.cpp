#include "EnemyDamageFactor.hpp"
namespace th143 {
i32 enemy_damage_factor_command(Emitters& actor,Vm& vm,VmHost& host){
    if(vm.instruction->opcode!=565)return -2;
    const float value=vm.float_argument(0,host);if(vm.failed)return -2;
    actor.put(0x40e0,word(value));return 0;
}
}

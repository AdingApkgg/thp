#include "EnemyDeathVisualConfig.hpp"
namespace th143 {
i32 enemy_death_visual_config(AnmView actor,Vm& vm,VmHost& host){
    if(!actor.data||vm.instruction->opcode!=323)return -2;
    const i32 selector=vm.integer_argument(0,host);if(vm.failed)return -2;
    actor.put(0x4088,u32(selector));
    const i32 script=vm.integer_argument(1,host);if(vm.failed)return -2;
    actor.put(0x4084,u32(script));return 0;
}
}


#include "EnemyPositionCopy.hpp"
namespace th143 {
i32 copy_enemy_position(AnmView target,Vm& vm,VmHost& host){
    u8* x=vm.reference(0,host,true);if(!x||vm.failed)return -2;
    const u32 px=target.get(0x44);std::memcpy(x,&px,4);
    u8* y=vm.reference(1,host,true);if(!y||vm.failed)return -2;
    const u32 py=target.get(0x48);std::memcpy(y,&py,4);
    return 0;
}
}

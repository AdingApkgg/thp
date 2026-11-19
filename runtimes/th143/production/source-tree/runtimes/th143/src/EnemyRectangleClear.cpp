#include "EnemyRectangleClear.hpp"
namespace th143 {
i32 enemy_rectangle_clear_command(AnmView v,Vm& vm,VmHost& host,u32 z,EnemyRectangleClearHost& services){
 if(!v.data||!vm.instruction||vm.instruction->opcode!=712)return -2;
 const float width=vm.float_argument(0,host),height=vm.float_argument(1,host);if(vm.failed)return -2;
 float angle;if(!services.enemy_rectangle_animation(v.get(0x124),angle))return -2;
 return services.enemy_rectangle_clear({v.floating(0x44),v.floating(0x48),v.floating(0x4c)},{width,height,real(z)},angle,1)?0:-2;
}
}

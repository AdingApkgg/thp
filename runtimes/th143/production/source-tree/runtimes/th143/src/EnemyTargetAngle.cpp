#include "EnemyTargetAngle.hpp"
#include <cmath>
namespace th143 {
i32 enemy_target_angle_command(Vm& vm,VmHost& host,EnemyTargetAngleHost& target){
 if(vm.instruction->opcode!=623)return -2;float x,y;if(!target.target_angle_position(x,y))return -2;const float point_y=vm.float_argument(2,host),dy=y-point_y;if(vm.failed)return -2;
 if(!target.target_angle_position(x,y))return -2;const float point_x=vm.float_argument(1,host),dx=x-point_x;if(vm.failed)return -2;const float angle=float(std::atan2(double(dy),double(dx)));
 auto* out=vm.reference(0,host,true);if(vm.failed||!out)return -2;const u32 value=word(angle);std::memcpy(out,&value,4);return 0;
}
}

#pragma once
#include "EclVm.hpp"
namespace th143 {
struct EnemyTargetAngleHost {virtual ~EnemyTargetAngleHost()=default;virtual bool target_angle_position(float& x,float& y)=0;};
i32 enemy_target_angle_command(Vm&,VmHost&,EnemyTargetAngleHost&);
}

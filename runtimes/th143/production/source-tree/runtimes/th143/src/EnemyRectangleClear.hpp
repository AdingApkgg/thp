#pragma once
#include "AnmState.hpp"
#include <array>
namespace th143 {
struct EnemyRectangleClearHost {
 virtual ~EnemyRectangleClearHost()=default;
 virtual bool enemy_rectangle_animation(u32 handle,float& angle)=0;
 virtual bool enemy_rectangle_clear(const std::array<float,3>& position,const std::array<float,3>& size,float angle,i32 kind)=0;
};
// ECL712 /425f86. The third size word is inherited caller-stack scratch;
// 417650 copies it to the manager even though its geometry uses only XY.
i32 enemy_rectangle_clear_command(AnmView,Vm&,VmHost&,u32 caller_size_z,EnemyRectangleClearHost&);
}

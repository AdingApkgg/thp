#pragma once
#include "AnmVm.hpp"
namespace th143 {
struct LaserKind0Host:AnmVmHost {virtual AnmView laser_animation_template(u32 resource,i32 script)=0;virtual bool laser_launch_sound(i32,float)=0;};
bool initialize_laser_kind0(u8*,u32,u32,const u8*,u32,u32,LaserKind0Host&);
}

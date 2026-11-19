#pragma once
#include "LaserKind1Initialize.hpp"
#include <functional>
namespace th143 {
struct LaserKind1UpdateServices {
 std::function<bool(std::array<float,3>&,bool&)> boss_position;
 std::function<bool(u32,bool)> contact;
};
bool update_laser_kind1(AnmView,u32,LaserKind1Host&,LaserKind1UpdateServices&,i32&);
}

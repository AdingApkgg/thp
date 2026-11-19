#pragma once
#include "AnmState.hpp"
#include <array>
namespace th143 {
struct LaserPathPoint {std::array<float,3> position;float speed,angle;};
bool laser_path_point(AnmView,float,LaserPathPoint&);
bool laser_path_previous(AnmView,const LaserPathPoint&,float,LaserPathPoint&);
}

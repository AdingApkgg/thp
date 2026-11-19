#pragma once
#include "LaserKind0Contact.hpp"
namespace th143 {
// Two untouched Z words at actual43ac60 entry ESP-18/ESP-24.
bool contact_laser_kind0_shared(AnmView,u32 token,bool forced,std::array<u32,2>& caller_scratch,LaserKind0ContactHost&);
}

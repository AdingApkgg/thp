#pragma once
#include "LaserKind0Initialize.hpp"
namespace th143 {
struct LaserKind0OrdinaryHost:LaserKind0Host {
 virtual bool laser_kind0_contact(u32 token,u32 argument)=0;
};
// Complete43a820 body for a transform-free laser. Nonempty transform rows
// and active transform flags stay unsupported until their separate binding.
bool update_laser_kind0_ordinary(AnmView,u32 token,LaserKind0OrdinaryHost&,i32& result);
}

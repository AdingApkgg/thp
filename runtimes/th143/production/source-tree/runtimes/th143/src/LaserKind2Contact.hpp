#pragma once
#include "LaserKind0Contact.hpp"
namespace th143 {
struct LaserKind2ContactHost:LaserKind0ContactHost {virtual bool laser_contact_read(u32,void*,u32)=0;};
bool contact_laser_kind2(AnmView,u32 token,bool forced,u32& caller_z_scratch,LaserKind2ContactHost&);
}

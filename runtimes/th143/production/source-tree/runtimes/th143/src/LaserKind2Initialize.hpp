#pragma once
#include "LaserKind0Initialize.hpp"
namespace th143 {
struct LaserKind2Host:LaserKind0Host {virtual bool laser_curve_allocate(u32 bytes,bool array,u32& token,u8*& storage)=0;};
bool initialize_laser_kind2(u8*,u32,u32,const u8*,u32,u32,LaserKind2Host&);
}

#pragma once
#include "AnmState.hpp"
namespace th143 {
struct LaserCurveNodeHost {
 virtual ~LaserCurveNodeHost()=default;
 virtual bool laser_node_read(u32,void*,u32)=0;
 virtual bool laser_node_write(u32,const void*,u32)=0;
 virtual bool laser_node_allocate(u32 bytes,u32& token,u8*& storage)=0;
};
bool append_laser_curve_node(u32 root,u32 time_bits,LaserCurveNodeHost&,u32& result);
}

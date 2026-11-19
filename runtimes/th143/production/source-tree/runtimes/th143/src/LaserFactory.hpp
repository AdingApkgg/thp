#pragma once
#include "LaserConstructor.hpp"
namespace th143 {
struct LaserFactoryHost {
 virtual ~LaserFactoryHost()=default;
 virtual bool laser_factory_read(u32,void*,u32)=0;
 virtual bool laser_factory_write(u32,const void*,u32)=0;
 virtual bool laser_factory_allocate(u32 bytes,u32& token,u8*& storage)=0;
 virtual bool laser_factory_initialize(u32 kind,u32 token,u32 parameters)=0;
};
bool create_laser(u32 manager,u32 kind,u32 parameters,LaserFactoryHost&,u32& result);
}

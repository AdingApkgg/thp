#pragma once
#include "Emitters.hpp"
namespace th143 {
struct LaserEmitterSink {virtual ~LaserEmitterSink()=default;virtual bool launch_laser(u32,const u8*,u32)=0;};
i32 laser_emitter_launch(Emitters&,Vm&,VmHost&,LaserEmitterSink&);
}

#pragma once
#include "AnmState.hpp"
namespace th143 {
struct FrameTimingCounterHost {
 virtual ~FrameTimingCounterHost()=default;
 virtual bool frame_counter_clock(double&)=0;
 virtual bool frame_counter_read(u32,void*,u32)=0;
 virtual bool frame_counter_write(u32,const void*,u32)=0;
};
// Full42bdc0; cached timing owner supplied by caller, clock46f4e0 is a service.
// Native presentation-loop call sites include46f1ee and46f411 after present.
bool update_frame_timing_counter(AnmView timing,FrameTimingCounterHost&);
}

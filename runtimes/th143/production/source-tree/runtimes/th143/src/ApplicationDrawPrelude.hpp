#pragma once
#include "AnmState.hpp"
namespace th143 {
struct ApplicationDrawPreludeHost {
 virtual ~ApplicationDrawPreludeHost()=default;
 virtual bool reset_application_batches()=0;
 virtual bool flush_application_batches()=0;
 virtual bool application_fog_state(u32 device,u32 kind,u32 value,u32& status)=0;
};
// Full444910, including reloading the device after the flush callback.
bool reset_application_draw_fog(AnmView,ApplicationDrawPreludeHost&,u32& result);
//46f2b3..46f2cc immediately before401670; scheduler dispatch follows separately.
bool prepare_application_draw_cycle(AnmView,ApplicationDrawPreludeHost&,u32& result);
}

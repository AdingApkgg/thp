#pragma once
#include "ApplicationFrame.hpp"
namespace th143 {
enum class ApplicationCompositionPass:u32 {
    First=0x445d10,SecondaryTarget=0x445e20,Second=0x445ec0,
    MainTarget=0x445fc0,Third=0x446060,InterfaceTarget=0x446110,
    Fourth=0x4461e0,Backbuffer=0x446240
};
struct ApplicationCompositionGlobals {
    u32 first_callback=0,second_callback=0;
    float scale=1;
    u32 logical_height=0,logical_width=0;
};
struct ApplicationCompositionServices {
    virtual ~ApplicationCompositionServices()=default;
    virtual bool composition_render_state(u32 device,u32 state,u32 value)=0;
    virtual bool draw_composition_animation(u32 manager,u32 animation)=0;
    virtual bool draw_composition_layer(u32 manager,u32 layer)=0;
    virtual bool invoke_composition_callback(u32 callback)=0;
};
// The eight original application composition callbacks. The application uses
// its actual shared layout: device +8, targets +1ac..1b4, VMs +1bc..1c8,
// primary camera +5b4, active camera +6e0/+6e4, ZWRITE cache +a04.
bool compose_application(AnmView,u32 self,u32 manager,ApplicationCompositionPass,
    ApplicationCompositionGlobals&,AnmRenderMemory&,AnmRenderDevice&,
    ApplicationFrameDevice&,ApplicationCompositionServices&);
}

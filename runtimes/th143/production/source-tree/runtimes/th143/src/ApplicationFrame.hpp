#pragma once
#include "AnmBatch.hpp"
#include <array>
namespace th143 {
struct ApplicationFrameGlobals {
    u32 device=0,render_target=0,clear_color=0,width=0,height=0;
    std::array<u32,4> stage_viewport{};
    std::array<i32,2> first_origin{};
    u32 logical_height=0,logical_width=0;
};
struct ApplicationClear {
    u32 rectangle_count=0,flags=3,color=0,depth=0x3f800000,stencil=0;
    std::array<i32,4> rectangle{};
};
struct ApplicationFrameDevice {
    virtual ~ApplicationFrameDevice()=default;
    virtual bool clear_application(u32 device,const ApplicationClear&)=0;
    virtual bool application_render_target(u32 device,u32 slot,u32 surface)=0;
    virtual bool application_transform(u32 device,u32 kind,const u8* matrix)=0;
    virtual bool application_viewport(u32 device,const u8* viewport)=0;
};
// 445b60 including445190. Owner spans at least6e8 bytes. Existing queued
// quads flush after cache invalidation, before the default camera transforms.
bool begin_application_frame(AnmView owner,u32 self,u32 manager,ApplicationFrameGlobals&,AnmRenderMemory&,AnmRenderDevice&,ApplicationFrameDevice&);
}

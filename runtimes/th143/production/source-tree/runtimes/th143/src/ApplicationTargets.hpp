#pragma once
#include "AnmBatch.hpp"
namespace th143 {
struct ApplicationTargetGlobals {u32 width=0;float scale=1;u32 auxiliary=0;};
struct ApplicationTargetServices {
    virtual ~ApplicationTargetServices()=default;
    virtual AnmView target_animation(u32 token)=0;
    virtual bool copy_target_template(u32 resource,i32 script,u32 animation)=0;
    virtual bool advance_target_animation(u32 animation)=0;
    virtual bool target_backbuffer(u32 device,u32& surface)=0;
    virtual bool target_surface(u32 texture,u32& surface)=0;
    virtual bool release_target_surface(u32 surface)=0;
};
// Original446460 and4466d0. Surface tokens and reference ownership remain
// device services; all owner/VM writes, selection and call ordering are native.
bool initialize_application_targets(AnmView,ApplicationTargetGlobals&,AnmRenderMemory&,ApplicationTargetServices&);
bool release_application_targets(AnmView,ApplicationTargetGlobals&,AnmRenderMemory&,ApplicationTargetServices&);
}

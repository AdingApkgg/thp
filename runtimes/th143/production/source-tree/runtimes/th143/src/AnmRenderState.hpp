#pragma once
#include "AnmBatch.hpp"
namespace th143 {
struct AnmSpriteDevice:AnmRenderDevice {
    virtual bool render_state(u32 state,u32 value)=0;
    virtual bool sampler_state(u32 sampler,u32 state,u32 value)=0;
    virtual bool texture(u32 stage,u32 token)=0;
};
// 479d50: blend, filtering and addressing caches; flush before each change.
bool configure_anm_render(u32 manager,u32 current_manager,AnmView,AnmRenderMemory&,AnmSpriteDevice&);
}

#pragma once
#include "AnmQuad.hpp"
#include <vector>
namespace th143 {
struct AnmRenderMemory {
    virtual ~AnmRenderMemory()=default;
    virtual bool read_render_memory(u32,void*,u32)=0;
    virtual bool write_render_memory(u32,const void*,u32)=0;
};
struct AnmRenderDevice {
    virtual ~AnmRenderDevice()=default;
    virtual bool texture_stage_state(u32 stage,u32 state,u32 value)=0;
    virtual bool vertex_format(u32 format)=0;
    virtual bool draw_triangles(u32 count,u32 stride,const u8* vertices,u32 bytes)=0;
};
// Original47a870,47a990,47aa90,47aac0 and47a8c0. Addresses are guest tokens;
// current-manager aliasing and the monotonic append cursor remain explicit.
bool initialize_anm_batches(u32 manager,AnmRenderMemory&);
bool append_anm_quad(u32 manager,const AnmQuad&,AnmRenderMemory&,u32& result);
bool reserve_anm_quad(u32 manager,AnmRenderMemory&,u32& token);
bool cancel_anm_quad(u32 manager,AnmRenderMemory&);
bool flush_anm_quads(u32 manager,u32 current_manager,AnmRenderMemory&,AnmRenderDevice&);
}

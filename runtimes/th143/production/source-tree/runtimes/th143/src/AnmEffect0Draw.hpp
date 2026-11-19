#pragma once
#include "AnmVm.hpp"
namespace th143 {
struct AnmEffect0DrawHost {
    virtual ~AnmEffect0DrawHost()=default;
    virtual bool effect0_flush()=0;
    virtual bool effect0_animation(AnmView)=0;
    virtual bool effect0_render_state(u32,u32)=0;
    virtual bool effect0_texture_stage(u32,u32,u32)=0;
    virtual bool effect0_vertex_format(u32)=0;
    virtual bool effect0_primitive(const u8*,u32)=0;
    virtual bool effect0_blend_cache(u8)=0;
};
//40a380, including the fixed playfield/full-window black backing passes.
bool draw_anm_effect0(u8* extra,u32 format,i32 width,i32 height,AnmEffect0DrawHost&);
}

#include "AnmEffect0Draw.hpp"
namespace th143 {
bool draw_anm_effect0(u8* extra,u32 format,i32 width,i32 height,AnmEffect0DrawHost& host){
    if(!extra)return false;const u32 mode=AnmView{extra}.get(0x1cfc);const bool backing=mode==2||(!mode&&format==21);
    if(backing){
        if(!host.effect0_flush())return false;
        for(const auto& state:std::array<std::array<u32,2>,8>{{{15,0},{206,1},{19,1},{20,2},{171,1},{207,2},{208,1},{209,1}}})if(!host.effect0_render_state(state[0],state[1]))return false;
        const float left=mode==2?128.f:0.f,top=mode==2?16.f:0.f,right=mode==2?512.f:float(width),bottom=mode==2?464.f:float(height);std::array<u8,80> vertices{};
        for(u32 i=0;i<4;++i){AnmView v{vertices.data()+i*20};v.put(0,word(i&1?right:left));v.put(4,word(i&2?bottom:top));v.put(8,0);v.put(12,word(1.f));v.put(16,0);}
        for(const auto& state:std::array<std::array<u32,2>,4>{{{4,2},{1,2},{5,0},{2,0}}})if(!host.effect0_texture_stage(0,state[0],state[1]))return false;
        if(!host.effect0_vertex_format(0x44)||!host.effect0_primitive(vertices.data(),vertices.size())||!host.effect0_render_state(15,1))return false;
        for(const auto& state:std::array<std::array<u32,2>,4>{{{4,4},{1,4},{5,2},{2,2}}})if(!host.effect0_texture_stage(0,state[0],state[1]))return false;
        if(!host.effect0_blend_cache(10)||!host.effect0_render_state(207,5)||!host.effect0_render_state(208,2)||!host.effect0_render_state(209,1))return false;
    }
    for(u32 i=0;i<4;++i)if(!host.effect0_animation({extra+i*AnmView::bytes}))return false;
    return !backing||(host.effect0_render_state(206,0)&&host.effect0_animation({extra+0x1730})&&host.effect0_flush());
}
}

#pragma once
#include "AnmEffect0Draw.hpp"
#include "GameRenderRuntime.hpp"
namespace th143 {
class GameAnmEffect0Draw final:public AnmEffect0DrawHost {
public:
    GameAnmEffect0Draw(GameRenderRuntime& render,GameRenderDevice& device,AnmResourceWorld& world):render(render),device(device),world(world){}
    bool draw(u8* extra,i32 width,i32 height){return draw_anm_effect0(extra,AnmView{render.application.data()}.get(0xfc),width,height,*this);}
private:
    GameRenderRuntime& render;GameRenderDevice& device;AnmResourceWorld& world;
    bool effect0_flush()override{return render.flush();}
    bool effect0_animation(AnmView vm)override{return render.draw_player_visual(0,vm);}
    bool effect0_render_state(u32 a,u32 b)override{return device.render_state(a,b);}
    bool effect0_texture_stage(u32 a,u32 b,u32 c)override{return device.texture_stage_state(a,b,c);}
    bool effect0_vertex_format(u32 v)override{return device.vertex_format(v);}
    bool effect0_primitive(const u8* p,u32 n)override{return device.primitive_upload(5,2,20,p,n);}
    bool effect0_blend_cache(u8 v)override{return world.write(0x72bc819c,&v,1);}
};
}

#include "th14-mode8-display-component-nov12.cpp"
#include "AnmRenderer.hpp"
struct EmbeddedQuadGraphics final:ZunGraphics {
 touhou::graphics::PipelineState state{};
 touhou::graphics::PipelineState& pipeline()override{return state;}
 u32 texture(const AnmResource&,u32)override{return 1;}
 void bind_texture(u32)override{}
 void set_layout(touhou::graphics::VertexLayout)override{}
 void set_matrix(touhou::graphics::MatrixKind,const Matrix4&)override{}
 void set_viewport(const GraphicsViewport&)override{}
 bool select_target(const AnmResource*,u32)override{return true;}
 bool clear_target(u32,const GraphicsViewport*,u32)override{return true;}
 void triangles(u32,const void*,u32)override{}
 void primitives(touhou::graphics::Topology,u32,const void*,u32)override{}
};
API(run_raw) u32 run_raw(){
 const u32* r=input+8;AnmVm vm{};fill(vm,r);const u32 nf=r[0x18/4];
 vm.flags|=(((nf>>21)&3)<<18)|(((nf>>23)&3)<<20);vm.set_drawing_mode((nf>>25)&31);
 vm.rotation={f(r[0x48/4]),f(r[0x4c/4]),f(r[0x50/4])};vm.sprite_size={f(r[0x80/4]),f(r[0x84/4])};
 vm.color=r[0x534/4];vm.secondary_color=r[0x538/4];vm.texture_scale={f(r[0x78/4]),f(r[0x7c/4])};vm.uv_matrix.identity();
 for(u32 i=0;i<4;++i)vm.uv[i]={f(r[(0x3b8+i*8)/4]),f(r[(0x3bc+i*8)/4])};
 AnmResource resource;AnmSprite sprite{};sprite.width=vm.sprite_size.x;sprite.height=vm.sprite_size.y;vm.sprite=&sprite;vm.resource=&resource;
 EmbeddedQuadGraphics graphics;AnmRenderer renderer(graphics);renderer.render_width=input[0];renderer.render_height=input[1];
 if(renderer.draw(vm)==-2)return 0;std::memcpy(output,vm.screen_quad_positions,48);return 12;
}

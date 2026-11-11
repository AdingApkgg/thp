#include "th14-mode8-display-component-nov12.cpp"
#include "AnmRenderer.hpp"
struct QuadDisplayGraphics final:ZunGraphics {
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
API(run_quad) u32 run_quad(u32 mode,u32 anchor,u32 ascii){
 if(mode>3||anchor>2||ascii>1)return 0;
 AnmVm vm{},parent{};fill(vm,input+8);fill(parent,input+8+371);if(input[7])vm.parent=&parent;
 vm.rotation.z=f(input[8+0x50/4]);parent.rotation.z=f(input[8+371+0x50/4]);
 constexpr u32 anchors[][2]={{0,0},{1,2},{2,1}};
 vm.flags|=(anchors[anchor][0]<<18)|(anchors[anchor][1]<<20);vm.set_drawing_mode(mode);
 vm.sprite_size={f(input[8+0x80/4]),f(input[8+0x84/4])};
 vm.color=0xff123456;vm.secondary_color=0xffabcdef;vm.texture_scale={1,1};vm.uv_matrix.identity();
 AnmResource resource;AnmSprite sprite{};sprite.width=vm.sprite_size.x;sprite.height=vm.sprite_size.y;vm.sprite=&sprite;vm.resource=&resource;
 QuadDisplayGraphics graphics;AnmRenderer renderer(graphics);renderer.render_width=input[0];renderer.render_height=input[1];
 const int status=ascii?renderer.draw_ascii_sprite(vm):renderer.draw(vm);if(status==-2)return 0;
 std::memcpy(output,vm.screen_quad_positions,48);return 12;
}

#include "th14-mode8-display-component-nov12.cpp"
#include "AnmRenderer.hpp"
struct Mode8Graphics final:ZunGraphics {
 touhou::graphics::PipelineState state{};Matrix4 world{};u32 world_calls=0,draw_calls=0;
 touhou::graphics::PipelineState& pipeline()override{return state;}
 u32 texture(const AnmResource&,u32)override{return 1;}
 void bind_texture(u32)override{}
 void set_layout(touhou::graphics::VertexLayout)override{}
 void set_matrix(touhou::graphics::MatrixKind kind,const Matrix4& m)override{if(kind==touhou::graphics::MatrixKind::World){world=m;++world_calls;}}
 void set_viewport(const GraphicsViewport&)override{}
 bool select_target(const AnmResource*,u32)override{return true;}
 bool clear_target(u32,const GraphicsViewport*,u32)override{return true;}
 void triangles(u32,const void*,u32)override{++draw_calls;}
 void primitives(touhou::graphics::Topology,u32,const void*,u32)override{++draw_calls;}
};
API(run_draw) u32 run_draw(){
 AnmVm vm{},parent{};fill(vm,input+8);fill(parent,input+8+371);if(input[7])vm.parent=&parent;
 vm.set_drawing_mode(8);vm.color=0xff123456;vm.secondary_color=0xffabcdef;
 AnmResource resource;AnmSprite sprite{};sprite.width=32;sprite.height=48;
 vm.sprite=&sprite;vm.resource=&resource;vm.texture_scale={1,1};vm.uv_matrix.identity();
 Mode8Graphics graphics;AnmRenderer renderer(graphics);renderer.render_width=input[0];renderer.render_height=input[1];
 const auto status=renderer.draw(vm);if(status!=0||graphics.world_calls!=1||graphics.draw_calls!=1)return 0;
 std::memcpy(output,graphics.world.m,64);std::memcpy(output+16,vm.transform_matrix.m,64);output[32]=vm.flags&12;return 33;
}

#include "AnmRenderer.hpp"
#include <cstdlib>
#include <cstring>
using namespace th11;using namespace touhou::graphics;
#define API(n) extern "C" __attribute__((export_name(#n)))
namespace {
struct Device final:ZunGraphics {
 PipelineState state{};Matrix4 world{};u32 count=0;
 PipelineState& pipeline()override{return state;}
 u32 texture(const AnmResource&,u32)override{return 1;}
 void bind_texture(u32)override{}void set_layout(VertexLayout)override{}
 void set_matrix(MatrixKind kind,const Matrix4& m)override{if(kind==MatrixKind::World){world=m;++count;}}
 // Effect8's pre-draw is followed by its ordinary screen-quad route.
 void triangles(u32,const void*,u32)override{}
 void primitives(Topology,u32,const void*,u32)override{}
 bool select_target(const AnmResource*,u32)override{return true;}
 bool clear_target(u32,const GraphicsViewport*,u32)override{return true;}
};
Device graphics;AnmRenderer renderer(graphics);AnmResource resource;AnmSprite sprite;
AnmTh14Ribbon ribbon{};AnmVm vm{},parent{};
}
API(output_ptr) const Matrix4* output_ptr(){return &graphics.world;}
API(run) i32 run(u32 width,u32 flags,u32 has_parent,float x,float y,float z,u32 route){
 renderer.invalidate();renderer.render_width=width;renderer.render_height=width*3/4;
 graphics.count=0;vm={};vm.flags=3;vm.flags2=flags;vm.color=0xffffffff;
 vm.resource=&resource;vm.sprite=&sprite;vm.geometry=&ribbon;
 vm.position={x,y,z};vm.script_position={1.125f,-2.5f,3.75f};vm.child_position={-4.25f,6.5f,-8.125f};
 vm.scale={2.25f,.75f};vm.extra_scale={1,1};vm.texture_scale={1,1};
 vm.parent=has_parent?&parent:nullptr;vm.integers[0]=40;
 vm.set_drawing_mode(route==0?23:route==1?24:0);vm.th13_effect=route==2?8:0;
 const int result=renderer.draw(vm);renderer.flush();return result==0&&graphics.count==1?1:result;
}

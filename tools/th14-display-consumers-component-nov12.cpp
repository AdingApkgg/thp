#include "ScreenFade.hpp"
#include "ScreenDeformation.hpp"
#include "AnmRenderer.hpp"
#include <cstring>
using namespace th11;using namespace touhou::graphics;
#define API(n) extern "C" __attribute__((export_name(#n)))
namespace {
struct Device final:ZunGraphics {
 PipelineState state{};GraphicsViewport viewport{};u32 data[20]{},submissions=0;
 PipelineState& pipeline()override{return state;}
 u32 texture(const AnmResource&,u32)override{return 1;}
 void bind_texture(u32)override{}void set_layout(VertexLayout)override{}
 void set_matrix(MatrixKind,const Matrix4&)override{}
 void set_viewport(const GraphicsViewport& v)override{viewport=v;}
 void triangles(u32,const void*,u32)override{std::abort();}
 void primitives(Topology t,u32 n,const void* p,u32 stride)override{
  if(t!=Topology::Strip||n!=2||stride!=20)std::abort();
  std::memcpy(data,p,80);++submissions;
 }
 bool select_target(const AnmResource*,u32)override{return true;}
 bool clear_target(u32,const GraphicsViewport*,u32)override{return true;}
};
Device graphics;AnmRenderer renderer(graphics);AnmManager manager;EnemyState enemy;
std::unique_ptr<ScreenDeformation> effect;u32 output[289*10+3];
void setup(u32 width){
 effect.reset();manager.clear();manager.render_space.scale=float(width)/640.f;
 manager.render_space.play_origin={float(width/2),float((width*3/4-448)/2)};
 effect=std::make_unique<ScreenDeformation>(manager);effect->vertices.resize(289);effect->positions.resize(289);
}
void capture(){
 u32* out=output;for(u32 i=0;i<289;++i){
  std::memcpy(out,&effect->positions[i],12);out+=3;
  std::memcpy(out,&effect->vertices[i],28);out+=7;
 }
 std::memcpy(out,&enemy.deformation_radius,4);++out;
 std::memcpy(out,&enemy.deformation_phase_x,4);++out;
 std::memcpy(out,&enemy.deformation_phase_y,4);
}
}
API(output_ptr) const u32* output_ptr(){return output;}
API(rectangle) u32 rectangle(u32 width,float x,float y,float w,float h){setup(width);effect->rectangle(x,y,w,h);capture();return 2890;}
API(begin) void begin(u32 width,float x,float y,float z,float radius,float rate){
 setup(width);manager.rate=rate;enemy={};enemy.current.position={x,y,z};
 enemy.deformation_target=128;enemy.deformation_radius=radius;enemy.deformation_color=0x008f8fff;
 enemy.deformation_phase_x=.25f;enemy.deformation_phase_y=-.5f;
}
API(tick) u32 tick(){effect->update(enemy,0);capture();return 2893;}
API(fade) u32 fade(u32 kind,u32 alpha,u32 color,u32 depth,u32 fog,u32 width,u32 height){
 renderer.invalidate();renderer.render_width=width;renderer.render_height=height;
 graphics.state={};graphics.state.depthWrite=depth;graphics.state.fog=fog;
 graphics.viewport={116,4,408,472,0,1};graphics.submissions=0;
 ScreenFade fade;fade.type=kind;fade.alpha=alpha;fade.color=color;fade.draw(renderer);renderer.flush();
 std::memcpy(output,graphics.data,80);std::memcpy(output+20,&graphics.viewport,24);
 return graphics.submissions==1?26:0;
}

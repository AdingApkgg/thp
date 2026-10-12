#include "th14-dialogue-portrait-sprite-fixture.cpp"
#include "../../cpp/game/AnmRenderer.hpp"
using namespace touhou::graphics;
struct PortraitGraphics final:ZunGraphics {
 PipelineState state{};u32 handle=0;bool valid=true;std::vector<u32> quads,materials;
 PipelineState& pipeline()override{return state;}
 u32 texture(const AnmResource&,u32 index)override{return index+1;}
 void bind_texture(u32 h)override{handle=h;}
 void set_layout(VertexLayout layout)override{if(layout!=VertexLayout::ScreenColorUv)valid=false;}
 void set_matrix(MatrixKind,const Matrix4&)override{valid=false;}
 void triangles(u32 count,const void* data,u32 stride)override{
  if(stride!=28||count%2){valid=false;return;}const auto* words=static_cast<const u32*>(data);
  for(u32 quad=0;quad<count/2;++quad){for(u32 i:{0,1,2,5})for(u32 f=0;f<7;++f)quads.push_back(words[(quad*6+i)*7+f]);
   const u32 a[]={handle,state.depthWrite,u32(state.sourceBlend)+1,u32(state.destinationBlend)+1,u32(state.blendEquation)+1,state.minFilter==Filter::Nearest?1u:2u,state.magFilter==Filter::Nearest?1u:2u,state.addressU==Address::Repeat?1u:state.addressU==Address::Mirror?2u:3u,state.addressV==Address::Repeat?1u:state.addressV==Address::Mirror?2u:3u};materials.insert(materials.end(),a,a+9);}
 }
 void primitives(Topology,u32,const void*,u32)override{valid=false;}
};
static PortraitGraphics portrait_graphics;static AnmRenderer portrait_renderer(portrait_graphics);
API(begin_geometry) i32 begin_geometry(u32 index,float rate,i32 immediate){portrait_renderer.invalidate();portrait_graphics.state={};portrait_graphics.handle=0;portrait_graphics.valid=true;portrait_graphics.quads.clear();portrait_graphics.materials.clear();portrait_renderer.viewport={0,0,640,480,0,1};portrait_renderer.offset={0,0};portrait_renderer.tint_enabled=false;return begin_sprite(index,rate,immediate);}
API(geometry_step) i32 geometry_step(){if(!sprite_step())return 0;portrait_graphics.quads.clear();portrait_graphics.materials.clear();for(u32 layer=0;layer<36;++layer)if(portrait_renderer.draw_layer(manager.layer_first(layer))!=1)return 0;portrait_renderer.flush();capture_sprite();return portrait_graphics.valid;}
API(geometry_count) u32 geometry_count(){return portrait_graphics.quads.size()/28;}
API(geometry_data) const u32* geometry_data(){return portrait_graphics.quads.data();}
API(geometry_materials) const u32* geometry_materials(){return portrait_graphics.materials.data();}

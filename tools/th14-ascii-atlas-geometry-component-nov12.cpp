#include "AsciiText.hpp"
#include "SceneCompositor.hpp"
#include <cstdlib>
#include <cstring>
using namespace th11;
using namespace touhou::graphics;
namespace {
AnmResource resource;std::vector<u32> records;u32 calls=0;
struct Graphics final:ZunGraphics {
 PipelineState state{};u32 bound=0,fvf=0;
 PipelineState& pipeline()override{return state;}
 u32 texture(const AnmResource& file,u32 index)override{if(&file!=&resource)std::abort();return index+1;}
 void bind_texture(u32 value)override{bound=value;}
 void set_layout(VertexLayout value)override{fvf=value==VertexLayout::ScreenColorUv?0x144:0;}
 void set_matrix(MatrixKind,const Matrix4&)override{}
 static u32 arg(const Argument& value){if(value.complement||value.alphaOnly)std::abort();return value.source==ArgumentSource::Diffuse?0:u32(value.source)+1;}
 void emit(u32 topology,u32 vertices,const void* data,u32 stride){
  const auto& p=state;++calls;
  records.insert(records.end(),{vertices,topology,stride,bound,fvf,u32(p.sourceBlend)+1,u32(p.destinationBlend)+1,u32(p.blendEquation)+1,u32(p.separateAlphaBlend),u32(p.separateAlphaBlend?p.sourceAlphaBlend:p.sourceBlend)+1,u32(p.separateAlphaBlend?p.destinationAlphaBlend:p.destinationBlend)+1,u32(p.separateAlphaBlend?p.alphaBlendEquation:p.blendEquation)+1,u32(p.alphaTest),u32(p.minFilter)+1,u32(p.magFilter)+1,u32(p.addressU)+1,u32(p.addressV)+1,u32(p.color.operation)+1,arg(p.color.first),arg(p.color.second),u32(p.alpha.operation)+1,arg(p.alpha.first),arg(p.alpha.second),p.textureTransform?2u:0u});
  const auto at=records.size();records.resize(at+vertices*stride/4);std::memcpy(records.data()+at,data,vertices*stride);
 }
 void triangles(u32 count,const void* data,u32 stride)override{emit(4,count*3,data,stride);}
 void primitives(Topology topology,u32 count,const void* data,u32 stride)override{emit(u32(topology)+1,count+2,data,stride);}
};
}
#define API(n) extern "C" __attribute__((export_name(#n)))
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(setup) u32 setup(const u8* bytes,u32 size){return resource.open(bytes,size);}
API(run) u32 run(u32 width,u32 height,i32 font,float sx,float sy,u32 shadow,i32 pass,i32 horizontal,i32 vertical){
 records.clear();calls=0;AnmManager manager;SceneCompositor compositor(manager);compositor.reset_cameras(true,width,height);Graphics graphics;graphics.initialize_game_pipeline();AnmRenderer renderer(graphics);renderer.upload_camera(compositor.full_camera);
 AsciiText text(resource);AsciiStyle style;style.font=font;style.scale={sx,sy};style.shadow=bool(shadow);style.pass=pass;style.horizontal=horizontal;style.vertical=vertical;style.color=0xa5345678;
 if(!text.add("A. 1,2s",{16.25f,28.5f,-.125f},style))return 0;
 style.font=(font+1)%6;style.scale={.75f,1.5f};style.shadow=!bool(shadow);style.color=0x803d7fbe;style.horizontal=style.vertical=1;
 if(!text.add("0.9",{620.25f,471.5f,0},style))return 0;
 return text.draw(renderer,pass,compositor.full_camera,compositor.play_camera);
}
API(data) const u32* data(){return records.data();}
API(words) u32 words(){return records.size();}
API(draw_calls) u32 draw_calls(){return calls;}

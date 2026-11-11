#include "AnmManager.hpp"
#include "AnmRenderer.hpp"
#include <cstdlib>
#include <cstring>
using namespace th11;
namespace {
AnmResource resource,ascii;AnmManager preparation;bool alpha=true;std::vector<u32> records;
struct Graphics final:ZunGraphics {
 touhou::graphics::PipelineState state{};
 touhou::graphics::PipelineState& pipeline()override{return state;}
 bool backbuffer_has_alpha()const noexcept override{return alpha;}
 u32 texture(const AnmResource&,u32 index)override{return index+1;}
 void bind_texture(u32)override{}
 void set_layout(touhou::graphics::VertexLayout)override{}
 void set_matrix(touhou::graphics::MatrixKind,const Matrix4&)override{}
 void emit(u32 topology,u32 vertices,const void* data,u32 stride){
  const auto& p=state;
  records.insert(records.end(),{topology,vertices,stride,u32(p.sourceBlend)+1,u32(p.destinationBlend)+1,u32(p.blendEquation)+1,u32(p.separateAlphaBlend),u32(p.separateAlphaBlend?p.sourceAlphaBlend:p.sourceBlend)+1,u32(p.separateAlphaBlend?p.destinationAlphaBlend:p.destinationBlend)+1,u32(p.separateAlphaBlend?p.alphaBlendEquation:p.blendEquation)+1,u32(p.alphaTest)});
  const auto at=records.size();records.resize(at+vertices*stride/4);std::memcpy(records.data()+at,data,vertices*stride);
 }
 void triangles(u32 count,const void* data,u32 stride)override{emit(4,count*3,data,stride);}
 void primitives(touhou::graphics::Topology topology,u32 count,const void* data,u32 stride)override{emit(u32(topology)+1,count+2,data,stride);}
};
}
#define API(n) extern "C" __attribute__((export_name(#n)))
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(setup) u32 setup(const u8* a,u32 n,const u8* b,u32 m){preparation.rate=1;preparation.script_rng={12345,0,0};preparation.visual_rng={54321,0,0};preparation.fallback_sprites=&ascii;return ascii.open(b,m)&&resource.open(a,n)&&preparation.prepare_resource(resource,8);}
API(run) u32 run(u32 state,u32 before,u32 frame,u32 format,u32 warm){
 alpha=format==21;records.clear();AnmManager env;env.rate=1;env.fallback_sprites=&ascii;env.script_rng=preparation.script_rng;env.visual_rng=preparation.visual_rng;
 AnmVm root;if(!root.copy_script(resource,0,8,&env.rate)||root.update(env)<0||!anm_th14_install_effect(root,0,env))return 0;
 root.interrupt(7+state);for(u32 i=0;i<before;++i)if(root.update(env))return 0;root.interrupt(1);for(u32 i=0;i<frame;++i)if(root.update(env))return 0;
 Graphics graphics;graphics.initialize_game_pipeline();AnmRenderer renderer(graphics);
 if(warm!=255){auto vm=static_cast<TransitionType0Th14*>(root.geometry)->embedded[4];vm.flags=(vm.flags&~0x70u)|(warm<<4)|3;vm.color=0xffffffff;if(renderer.draw(vm)==-2)return 0;renderer.flush();records.clear();}
 const int status=renderer.draw(root);renderer.flush();return status!=-2;
}
API(data) const u32* data(){return records.data();}
API(words) u32 words(){return records.size();}

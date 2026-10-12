#include "../../cpp/game/Stage.hpp"
#include "render-fixture.hpp"
using namespace th11;using namespace th11::test;
static AnmManager manager;static AnmResource animations,text;static u32 background=0;
static Stage stage(manager,animations,text,background,3);static RecordingGraphics graphics;static AnmRenderer renderer(graphics);static SceneCamera camera;static AnmSprite sprite;
static AnmTh14Ribbon ribbon;static std::vector<u32> submissions;static std::vector<u32> calls;static std::vector<AnmVertex> quads;static std::vector<u32> states;
extern "C" int __real__ZN4th1111AnmRenderer4drawERNS_5AnmVmE(AnmRenderer*,AnmVm&);
extern "C" int __wrap__ZN4th1111AnmRenderer4drawERNS_5AnmVmE(AnmRenderer* r,AnmVm& vm){
 calls.insert(calls.end(),{u32(&vm-stage.state.script_animations),u32(graphics.state.depthWrite),u32(graphics.state.fog),u32(r->camera.projection.m[5]>5)});
 return __real__ZN4th1111AnmRenderer4drawERNS_5AnmVmE(r,vm);
}
#define API(name) extern "C" __attribute__((export_name(#name)))
API(run) u32 run(u32 layer,u32 mode,u32 depth,u32 fog,u32 mask,u32 pattern,u32 visibility,u32 callbacks,u32 depth_mask){
 renderer.invalidate();graphics.data.clear();graphics.submissions.clear();graphics.snapshots.clear();calls.clear();quads.clear();states.clear();stage.state={};stage.resource={};graphics.state={};graphics.state.depthWrite=depth;graphics.state.fog=fog;
 camera={};camera.position={0,0,-600};camera.direction=camera.reserved24={0,0,1};camera.viewport={116,4,408,472,0,1};renderer.set_camera(camera,false);sprite.width=32;sprite.height=48;
 for(u32 n=0;n<80;++n)ribbon.vertices[n]={{float(n*.37),float(double(-int(n))*.71),float(n*1.3)},0x80123456,{float(double(n)/80),.25f}};
 for(u32 i=0;i<8;++i){auto& vm=stage.state.script_animations[i];vm.flags=visibility&(1<<(i%2))?3:0;vm.flags|=depth_mask&(1<<(i%2))?0x800:0;vm.th13_effect=callbacks&(1<<(i%2))?8:0;vm.geometry=&ribbon;vm.uv_matrix.identity();vm.set_drawing_mode(mode);vm.sprite=mask&(1<<i)?&sprite:nullptr;vm.resource=&animations;vm.scale=vm.extra_scale=vm.texture_scale={1,1};vm.sprite_size={32,48};vm.position={180.f+i*24,100.f+i*20,.375f};vm.color=vm.inherited_color=0xff123456;vm.secondary_color=0xffabcdef;vm.uv[0]={0,0};vm.uv[1]={1,0};vm.uv[2]={0,1};vm.uv[3]={1,1};stage.state.script_animation_layers[i]=pattern==0?layer:i;}
 const bool ok=stage.draw_layer(renderer,camera,layer);renderer.flush();
 submissions.clear();for(u32 i=0;i<graphics.submissions.size();++i){const auto& draw=graphics.submissions[i];const auto& p=graphics.snapshots[i];const auto* words=reinterpret_cast<const u32*>(graphics.data.data()+draw.start);
  if(draw.stride==28){for(u32 q=0;q<draw.count/2;++q){submissions.insert(submissions.end(),{0,p.depth_write,p.fog});for(u32 index:{0u,1u,2u,5u})submissions.insert(submissions.end(),words+(q*6+index)*7,words+(q*6+index)*7+7);}}
  else{if(draw.stride!=24)return 0;submissions.insert(submissions.end(),{1,draw.topology+1,draw.count,draw.stride,p.depth_write,p.fog});const auto* w=reinterpret_cast<const u32*>(p.world.m);const auto* uv=reinterpret_cast<const u32*>(p.uv.m);submissions.insert(submissions.end(),w,w+16);submissions.insert(submissions.end(),uv,uv+16);submissions.insert(submissions.end(),words,words+draw.size/4);}
 }
 return ok;
}
API(call_data) const u32* call_data(){return calls.data();}API(call_words) u32 call_words(){return calls.size();}
API(submission_data) const u32* submission_data(){return submissions.data();}API(submission_words) u32 submission_words(){return submissions.size();}
API(final_state) u32 final_state(u32 field){return field?graphics.state.fog:graphics.state.depthWrite;}

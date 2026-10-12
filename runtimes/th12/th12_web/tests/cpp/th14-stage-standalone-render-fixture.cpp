#include "../../cpp/game/Stage.hpp"
#include "render-fixture.hpp"
using namespace th11;using namespace th11::test;
static AnmManager manager;static AnmResource animations,text;static u32 background=0;
static Stage stage(manager,animations,text,background,3);static RecordingGraphics graphics;static AnmRenderer renderer(graphics);static SceneCamera camera;static AnmSprite sprite;
static std::vector<u32> calls;static std::vector<AnmVertex> quads;static std::vector<u32> states;
extern "C" int __real__ZN4th1111AnmRenderer4drawERNS_5AnmVmE(AnmRenderer*,AnmVm&);
extern "C" int __wrap__ZN4th1111AnmRenderer4drawERNS_5AnmVmE(AnmRenderer* r,AnmVm& vm){
 calls.insert(calls.end(),{u32(&vm-stage.state.script_animations),u32(graphics.state.depthWrite),u32(graphics.state.fog),u32(r->camera.projection.m[5]>5)});
 return __real__ZN4th1111AnmRenderer4drawERNS_5AnmVmE(r,vm);
}
#define API(name) extern "C" __attribute__((export_name(#name)))
API(run) u32 run(u32 layer,u32 mode,u32 depth,u32 fog,u32 mask,u32 pattern){
 renderer.invalidate();graphics.data.clear();graphics.submissions.clear();graphics.snapshots.clear();calls.clear();quads.clear();states.clear();stage.state={};stage.resource={};graphics.state={};graphics.state.depthWrite=depth;graphics.state.fog=fog;
 camera={};camera.position={0,0,-600};camera.direction=camera.reserved24={0,0,1};camera.viewport={116,4,408,472,0,1};renderer.set_camera(camera,false);sprite.width=32;sprite.height=48;
 for(u32 i=0;i<8;++i){auto& vm=stage.state.script_animations[i];vm.flags=3;vm.set_drawing_mode(mode);vm.sprite=mask&(1<<i)?&sprite:nullptr;vm.resource=&animations;vm.scale=vm.extra_scale=vm.texture_scale={1,1};vm.sprite_size={32,48};vm.position={180.f+i*24,100.f+i*20,.375f};vm.color=vm.inherited_color=0xff123456;vm.secondary_color=0xffabcdef;vm.uv[0]={0,0};vm.uv[1]={1,0};vm.uv[2]={0,1};vm.uv[3]={1,1};stage.state.script_animation_layers[i]=pattern==0?layer:i;}
 const bool ok=stage.draw_layer(renderer,camera,layer);renderer.flush();
 for(u32 i=0;i<graphics.submissions.size();++i){const auto& s=graphics.submissions[i];const auto& p=graphics.snapshots[i];const auto* v=reinterpret_cast<const AnmVertex*>(graphics.data.data()+s.start);
  for(u32 n=0;n<s.count/2;++n){for(u32 index:{0u,1u,2u,5u})quads.push_back(v[n*6+index]);states.insert(states.end(),{p.depth_write,p.fog});}
 }
 return ok;
}
API(call_data) const u32* call_data(){return calls.data();}API(call_words) u32 call_words(){return calls.size();}
API(quad_count) u32 quad_count(){return quads.size()/4;}
API(vertex) float vertex(u32 q,u32 i,u32 field){const auto& v=quads[q*4+i];switch(field){case 0:return v.position.x;case 1:return v.position.y;case 2:return v.position.z;case 3:return v.reciprocal_w;case 5:return v.uv.x;default:return v.uv.y;}}
API(color) u32 color(u32 q,u32 i){return quads[q*4+i].color;}
API(quad_state) u32 quad_state(u32 q,u32 field){return states[q*2+field];}
API(final_state) u32 final_state(u32 field){return field?graphics.state.fog:graphics.state.depthWrite;}

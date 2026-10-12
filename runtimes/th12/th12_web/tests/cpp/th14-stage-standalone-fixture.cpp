#include "../../cpp/game/Stage.hpp"
#include "render-fixture.hpp"
#include <cstdlib>
using namespace th11;using namespace th11::test;
static AnmManager manager;static AnmResource animations,text;static u32 background=0;
static Stage stage(manager,animations,text,background,3);static RecordingGraphics graphics;static AnmRenderer renderer(graphics);static SceneCamera camera;static AnmSprite sprite;
static std::vector<u32> draws,assignments,events;
extern "C" int __real__ZN4th1111AnmRenderer4drawERNS_5AnmVmE(AnmRenderer*,AnmVm&);
extern "C" int __wrap__ZN4th1111AnmRenderer4drawERNS_5AnmVmE(AnmRenderer* r,AnmVm& vm){
 auto& p=r->pipeline();draws.insert(draws.end(),{u32(&vm-stage.state.script_animations),u32(p.depthWrite),u32(p.fog),u32(r->camera.projection.m[5]>5)});
 return __real__ZN4th1111AnmRenderer4drawERNS_5AnmVmE(r,vm);
}
struct ScriptWorld final:StageScriptWorld{
 bool stage_animation(AnmVm& vm,i32 script)override{events.insert(events.end(),{u32(&vm-stage.state.script_animations),u32(script)});return true;}
 bool stage_deformation(i32)override{return true;}void stage_color(u32)override{}
};
static ScriptWorld world;
static StageResource timeline_resource;
#define API(name) extern "C" __attribute__((export_name(#name)))
API(allocate) void* allocate(u32 n){return std::malloc(n);}API(release) void release(void* p){std::free(p);}
API(begin) u32 begin(const u8* p,u32 n){
 stage.state={};stage.state.camera.position={0,0,-600};stage.state.camera.direction={0,300,600};stage.state.camera.up={0,1,0};stage.state.script_timer.set(0,&manager.rate);
 return timeline_resource.open(p,n);
}
API(tick) u32 tick(){
 events.clear();assignments.clear();if(!stage_script(stage.state,timeline_resource,&manager.rate,world))return 0;
#if defined(TH14_STANDALONE_FIXED)
 for(u32 i=0;i<8;++i)assignments.push_back(stage.state.script_animation_layers[i]);
#else
 assignments.resize(8);
#endif
 assignments.push_back(stage.state.script_timer.current);assignments.push_back(stage.state.instruction_offset);assignments.insert(assignments.end(),events.begin(),events.end());return 1;
}
API(script) u32 script(u32 slot,i32 id,u32 layer){
 stage.state={};events.clear();assignments.clear();stage.state.script_animations[slot].flags=1;
 StageResource resource;StageInstruction assign;assign.opcode=14;assign.length=20;assign.arguments={slot,u32(id),layer};resource.instructions.push_back(assign);
 StageInstruction stop;stop.opcode=0;stop.length=8;stop.offset=20;resource.instructions.push_back(stop);
 if(!stage_script(stage.state,resource,&manager.rate,world))return 0;
 for(u32 i=0;i<8;++i){
#if defined(TH14_STANDALONE_FIXED)
  assignments.push_back(stage.state.script_animation_layers[i]);
#else
  assignments.push_back(0);
#endif
 }
 assignments.push_back((stage.state.script_animations[slot].flags&1)!=0);assignments.insert(assignments.end(),events.begin(),events.end());return 1;
}
API(run) u32 run(u32 layer,u32 depth,u32 fog,u32 mask,u32 pattern){
 stage.state={};stage.resource={};draws.clear();graphics.state={};graphics.state.depthWrite=depth;graphics.state.fog=fog;renderer.invalidate();
 camera={};camera.position={0,0,-600};camera.direction=camera.reserved24={0,0,1};camera.viewport={116,4,408,472,0,1};renderer.set_camera(camera,false);
 for(u32 i=0;i<8;++i){auto& vm=stage.state.script_animations[i];vm.sprite=mask&(1<<i)?&sprite:nullptr;
#if defined(TH14_STANDALONE_FIXED)
  stage.state.script_animation_layers[i]=pattern==0?layer:pattern==1?i:(layer+i)%12;
#endif
 }
 return stage.draw_layer(renderer,camera,layer);
}
API(data) const u32* data(){return assignments.data();}API(words) u32 words(){return assignments.size();}
API(draw_data) const u32* draw_data(){return draws.data();}API(draw_words) u32 draw_words(){return draws.size();}
API(field) u32 field(u32 i){return i==0?graphics.state.depthWrite:i==1?graphics.state.fog:u32(renderer.camera.projection.m[5]>5);}

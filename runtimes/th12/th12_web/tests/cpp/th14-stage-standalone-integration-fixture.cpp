#include "../../cpp/game/Stage.hpp"
#include "../../cpp/game/SceneCompositor.hpp"
#include "../../cpp/game/ScreenFade.hpp"
#include "render-fixture.hpp"
#include <cstdlib>
#include <cmath>
using namespace th11;
using namespace th11::test;
static AnmManager manager;
static AnmResource animation,text;
static SceneCompositor compositor(manager);
static RecordingGraphics graphics;
static AnmRenderer renderer(graphics);
static ScreenFades fades;
static std::unique_ptr<Stage> stage;
static std::string error;
static std::vector<u32> standalone_draws;
extern "C" int __real__ZN4th1111AnmRenderer4drawERNS_5AnmVmE(AnmRenderer*,AnmVm&);
extern "C" int __wrap__ZN4th1111AnmRenderer4drawERNS_5AnmVmE(AnmRenderer* r,AnmVm& vm){
 for(u32 i=0;stage&&i<8;++i)if(&vm==&stage->state.script_animations[i]){
  SceneCamera screen=stage->state.camera;screen.screen();
  const bool screen_mode=r->camera.projection.m[5]==screen.projection.m[5];
  standalone_draws.insert(standalone_draws.end(),{i,u32(stage->state.script_animation_layers[i]),u32(screen_mode)});
 }
 return __real__ZN4th1111AnmRenderer4drawERNS_5AnmVmE(r,vm);
}
#define API(name) extern "C" __attribute__((export_name(#name)))
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(open_resource) i32 open_resource(u32 which,const u8* p,u32 n,u32 number){
 if(!which){stage.reset();manager.clear();renderer.invalidate();}
 auto& file=which?text:animation;
 if(!file.open(p,n)){error="invalid original ANM resource";return 0;}
 if(!manager.prepare_resource(file,which?0:u16((number&1)+3))){error=manager.last_error_text();return 0;}
 return 1;
}
API(start) i32 start(const u8* p,u32 n,i32 number){
 error.clear();StageResource resource;if(!resource.open(p,n)){error=resource.error;return 0;}
 if(!compositor.initialize(text)){error=compositor.last_error;return 0;}
 stage=std::make_unique<Stage>(manager,animation,text,compositor.clear_color,u16((number&1)+3));
 stage->active_camera=&compositor.world_camera;
 if(!stage->initialize(resource,number,compositor.world_camera)){error=stage->error;return 0;}return 1;
}
API(tick) i32 tick(){
 standalone_draws.clear();
 graphics.data.clear();graphics.submissions.clear();graphics.snapshots.clear();graphics.target_events.clear();
 if(!stage->update()){error=stage->error;return 0;}
 if(!manager.update(false)||!manager.update(true)){error=manager.last_error_text();return 0;}
 if(!stage->draw_background(renderer,compositor.world_camera,fades)||!stage->draw_foreground(renderer,compositor.world_camera)){error=stage->error;return 0;}
 renderer.flush();for(const auto& snapshot:graphics.snapshots)if(!std::isfinite(snapshot.world.m[0])){error="nonfinite stage transform";return 0;}
 if(graphics.state.rangeFog){error="unexpected range fog";return 0;}return 1;
}
API(last_error) const char* last_error(){return error.c_str();}
API(count) u32 count(u32 kind){
 if(kind==0)return stage->state.frame_count;if(kind==1)return graphics.submissions.size();
 if(kind==2)return stage->state.drawn_primitives;if(kind==3)return stage->state.drawn_objects;
 if(kind==4)return stage->state.culled_objects;if(kind==5)return graphics.data.size();
 return manager.active_count();
}

API(standalone_data) const u32* standalone_data(){return standalone_draws.data();}
API(standalone_words) u32 standalone_words(){return standalone_draws.size();}
API(slot_layer) u32 slot_layer(u32 i){return stage->state.script_animation_layers[i];}
API(slot_sprite) u32 slot_sprite(u32 i){return stage->state.script_animations[i].sprite!=nullptr;}
API(script_time) u32 script_time(){return stage->state.script_timer.current;}
API(script_offset) u32 script_offset(){return stage->state.instruction_offset;}

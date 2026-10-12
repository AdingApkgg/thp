#include "../../cpp/game/Stage.hpp"
#include "../../cpp/game/SceneCompositor.hpp"
#include "../../cpp/game/ScreenFade.hpp"
#include "render-fixture.hpp"
#include <cstdlib>
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
#define API(name) extern "C" __attribute__((export_name(#name)))
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(open_resource) i32 open_resource(u32 which,const u8* p,u32 n){
    if(!which){stage.reset();manager.clear();renderer.invalidate();}
    return (which?text:animation).open(p,n);
}
API(start) i32 start(const u8* p,u32 n,i32 number){
    error.clear();StageResource resource;if(!resource.open(p,n)){error=resource.error;return 0;}
    if(!compositor.initialize(text)){error="compositor initialization";return 0;}compositor.reset_cameras(true);
    stage=std::make_unique<Stage>(manager,animation,text,compositor.clear_color,3);
    stage->active_camera=&compositor.world_camera;
    if(!stage->initialize(resource,number,compositor.world_camera)){error=stage->error;return 0;}return 1;
}
API(tick) i32 tick(){
    graphics.data.clear();graphics.submissions.clear();graphics.snapshots.clear();graphics.target_events.clear();
    if(!stage->update()){error=stage->error;return 0;}
    if(!manager.update(false)||!manager.update(true)){error="ANM opcode "+std::to_string(manager.last_error);return 0;}
    if(!stage->draw_background(renderer,compositor.world_camera,fades)||!stage->draw_foreground(renderer,compositor.world_camera)){error=stage->error;return 0;}
    renderer.flush();return 1;
}
API(last_error) const char* last_error(){return error.c_str();}
API(count) u32 count(u32 kind){
    if(kind==0)return stage->state.frame_count;if(kind==1)return graphics.submissions.size();
    if(kind==2)return stage->state.drawn_primitives;
    u32 n=0;for(const auto& s:graphics.submissions)if(s.stride==24&&s.count==30)++n;return n;
}

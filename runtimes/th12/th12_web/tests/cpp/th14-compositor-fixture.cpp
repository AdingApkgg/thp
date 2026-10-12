#include "../../cpp/game/SceneCompositor.hpp"
#include "render-fixture.hpp"
#include <cstdlib>
using namespace th11;
using namespace th11::test;
static AnmManager manager;
static AnmResource resource;
static SceneCompositor compositor(manager);
static RecordingGraphics graphics;
static AnmRenderer renderer(graphics);
static AnmSprite sprite;
#define API(name) extern "C" __attribute__((export_name(#name)))
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(open_resource) i32 open_resource(const void* p,u32 n){return resource.open(static_cast<const u8*>(p),n);}
API(initialize) i32 initialize(u32 width,u32 height){return compositor.initialize(resource,width,height);}
API(copy_script) i32 copy_script(u32 i){return compositor.copies[i].script_index;}
API(copy_filter) u32 copy_filter(u32 i){return compositor.copies[i].flags>>31;}
API(camera_value) float camera_value(u32 camera,u32 field){const auto& v=camera==0?compositor.play_camera.viewport:camera==1?compositor.scaled_play_camera.viewport:camera==2?compositor.full_camera.viewport:compositor.world_camera.viewport;switch(field){case 0:return v.x;case 1:return v.y;case 2:return v.width;case 3:return v.height;case 4:return v.near_depth;default:return v.far_depth;}}
API(pass_count) u32 pass_count(){return sizeof(scene_draw_passes)/sizeof(scene_draw_passes[0]);}
API(pass_value) u32 pass_value(u32 i,u32 field){const auto& p=scene_draw_passes[i];return field==0?p.priority:field==1?u32(p.kind):p.layer;}
static bool add_layer(u32 layer){
    auto* vm=manager.create(resource,compositor.copies[0].script_index,0,layer,layer>=34);if(!vm)return false;
    vm->layer=layer;vm->sprite=&sprite;sprite.width=sprite.height=12;sprite.texture=0;
    vm->sprite_size={12,12};vm->flags=15;vm->flags2=0;vm->th13_native_flags=0;vm->position={200,100,0};vm->script_position=vm->child_position={};vm->scale=vm->extra_scale={1,1};vm->pivot={};vm->color=0xffffffff;
    vm->instruction=nullptr;return manager.update(layer>=34);
}
API(draw_pass) i32 draw_pass(u32 i){
    renderer.flush();manager.clear();const auto& p=scene_draw_passes[i];
    if(p.kind==SceneDrawKind::Animation&&!add_layer(p.layer))return -1;
    if(p.kind==SceneDrawKind::CompositeA&&!add_layer(32))return -2;
    graphics.target_events.clear();graphics.submissions.clear();graphics.snapshots.clear();graphics.viewports.clear();graphics.data.clear();compositor.clear_color=0;
    const bool result=p.kind==SceneDrawKind::Animation?compositor.draw_animation(renderer,p.layer):compositor.draw(renderer,p.kind);renderer.flush();return result;
}
API(event_count) u32 event_count(){return graphics.target_events.size();}
API(event_value) u32 event_value(u32 i,u32 field){const auto& e=graphics.target_events[i];switch(field){case 0:return e.kind;case 1:return e.target;case 2:return e.color;case 3:return e.count;case 4:return e.rectangle.x;case 5:return e.rectangle.y;case 6:return e.rectangle.width;case 7:return e.rectangle.height;default:return e.flags;}}
API(viewport_count) u32 viewport_count(){return graphics.viewports.size();}
API(viewport_value) float viewport_value(u32 i,u32 field){const auto& v=graphics.viewports[i];switch(field){case 0:return v.x;case 1:return v.y;case 2:return v.width;case 3:return v.height;case 4:return v.near_depth;default:return v.far_depth;}}
API(draw_count) u32 draw_count(){return graphics.submissions.size();}
API(draw_value) float draw_value(u32 i,u32 field){const auto& s=graphics.submissions[i];const auto* v=reinterpret_cast<const AnmVertex*>(graphics.data.data()+s.start);switch(field){case 0:return s.target;case 1:return s.texture;case 2:return s.count;case 3:return v->position.x;case 4:return v->position.y;case 5:return v->uv.x;default:return v->uv.y;}}
API(draw_alpha) u32 draw_alpha(u32 i){return graphics.snapshots[i].alpha_test;}
API(alpha_restored) u32 alpha_restored(){return graphics.state.alphaTest;}
API(copy_color) u32 copy_color(u32 i){return compositor.copies[i].color;}

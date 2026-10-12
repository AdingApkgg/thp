#include "../../cpp/game/Stage.hpp"
#include "../../cpp/game/ScreenFade.hpp"
#include "render-fixture.hpp"
using namespace th11;using namespace th11::test;
static AnmManager manager;static AnmResource animations,text;static u32 bg=0;
static Stage old_stage(manager,animations,text,bg,3),new_stage(manager,animations,text,bg,3);
static RecordingGraphics graphics;static AnmRenderer renderer(graphics);static SceneCamera camera;static ScreenFades fades;static u32 created=0;static std::vector<u32> stage_fields;
static u32 word(float x){u32 v;std::memcpy(&v,&x,4);return v;}
static void reset_draw(){renderer.flush();graphics.data.clear();graphics.submissions.clear();graphics.snapshots.clear();}
static void draw(){reset_draw();fades.draw(renderer,10);renderer.flush();}
static u32 create(u32 kind){auto& stage=created++?new_stage:old_stage;stage.state={};stage.resource={};stage.object_animations.clear();stage.state.camera=camera;stage.state.draw_distance_squared=9610000;stage.state.effects_enabled=3;stage.state.tint=0xffffff;stage.state.draw_flags=kind==3?4:1;stage.state.fade_timer.set(0,&manager.rate);
 renderer.tint_enabled=false;renderer.tint=0x80808080;if(kind==3){if(!stage.draw_background(renderer,camera,fades))return 0;}else stage.fade_out(fades);const auto& s=stage.state;stage_fields={s.draw_flags,u32(s.fade_timer.previous),u32(s.fade_timer.current),word(s.fade_timer.fractional)};draw();return fades.effects.size();}
#define API(name) extern "C" __attribute__((export_name(#name)))
API(start) u32 start(u32 kind,float rate){renderer.invalidate();manager.rate=rate;fades.effects.clear();created=0;graphics.state={};graphics.state.depthWrite=false;graphics.state.fog=false;graphics.state.depthCompare=touhou::graphics::Compare::Always;reset_draw();camera={};camera.position={0,0,-600};camera.direction=camera.reserved24={0,0,1};camera.viewport={116,4,408,472,0,1};camera.fog.set(0xff605070,1000,5000);return create(kind);}
API(add) u32 add(u32 kind){return create(kind);}
API(tick) u32 tick(u32 stopped,u32 frozen){reset_draw();fades.update(stopped,frozen);fades.draw(renderer,10);renderer.flush();return fades.effects.size();}
API(count) u32 count(){return fades.effects.size();}
API(field) u32 field(u32 i){const auto& e=fades.effects[i/8];u32 f[]={u32(e.type),u32(e.duration),u32(e.alpha),e.color,e.priority,u32(e.timer.previous),u32(e.timer.current),word(e.timer.fractional)};return f[i%8];}
API(stage_field) u32 stage_field(u32 i){return stage_fields[i];}
API(vertices) const u8* vertices(){return graphics.data.data();}API(vertex_words) u32 vertex_words(){return graphics.data.size()/4;}

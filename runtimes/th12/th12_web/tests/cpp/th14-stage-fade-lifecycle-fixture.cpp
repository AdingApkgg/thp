#include "../../cpp/game/Stage.hpp"
#include "../../cpp/game/ScreenFade.hpp"
#include "render-fixture.hpp"
using namespace th11;using namespace th11::test;
static AnmManager manager;static AnmResource animations,text;static u32 bg=0;static Stage stage(manager,animations,text,bg,3);static RecordingGraphics graphics;static AnmRenderer renderer(graphics);static SceneCamera camera;static ScreenFades fades;static std::vector<u32> initial;
static u32 word(float x){u32 v;std::memcpy(&v,&x,4);return v;}
static std::vector<u32> fields(){if(fades.effects.empty())return {};const auto& e=fades.effects[0];return {u32(e.type),u32(e.duration),u32(e.alpha),e.color,e.priority,u32(e.timer.previous),u32(e.timer.current),word(e.timer.fractional)};}
static void reset_draw(){renderer.flush();graphics.data.clear();graphics.submissions.clear();graphics.snapshots.clear();}
#define API(name) extern "C" __attribute__((export_name(#name)))
API(start) u32 start(u32 kind,float rate){renderer.invalidate();manager.rate=rate;stage.state={};stage.resource={};stage.object_animations.clear();fades.effects.clear();graphics.state={};graphics.state.depthWrite=false;graphics.state.fog=false;graphics.state.depthCompare=touhou::graphics::Compare::Always;reset_draw();renderer.tint_enabled=false;renderer.tint=0x80808080;
 camera={};camera.position={0,0,-600};camera.direction=camera.reserved24={0,0,1};camera.viewport={116,4,408,472,0,1};camera.fog.set(0xff605070,1000,5000);stage.state.camera=camera;stage.state.draw_distance_squared=9610000;stage.state.effects_enabled=3;stage.state.tint=0xffffff;stage.state.draw_flags=kind==3?4:1;stage.state.fade_timer.set(0,&manager.rate);
 if(kind==3){if(!stage.draw_background(renderer,camera,fades))return 0;}else stage.fade_out(fades);initial=fields();const auto& s=stage.state;initial.insert(initial.end(),{s.draw_flags,u32(s.fade_timer.previous),u32(s.fade_timer.current),word(s.fade_timer.fractional)});reset_draw();fades.draw(renderer,10);renderer.flush();return fades.effects.size();}
API(tick) u32 tick(u32 stopped,u32 frozen){reset_draw();fades.update(stopped,frozen);fades.draw(renderer,10);renderer.flush();return fades.effects.size();}
API(initial_field) u32 initial_field(u32 i){return initial[i];}API(field) u32 field(u32 i){return fields()[i];}API(vertices) const u8* vertices(){return graphics.data.data();}API(vertex_words) u32 vertex_words(){return graphics.data.size()/4;}

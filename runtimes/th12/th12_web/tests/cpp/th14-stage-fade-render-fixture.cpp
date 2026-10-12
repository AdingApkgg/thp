#include "../../cpp/game/ScreenFade.hpp"
#include "render-fixture.hpp"
using namespace th11;using namespace th11::test;
static RecordingGraphics graphics;static AnmRenderer renderer(graphics);
#define API(name) extern "C" __attribute__((export_name(#name)))
API(run) u32 run(u32 kind,u32 alpha,u32 color,u32 depth,u32 fog){renderer.invalidate();graphics.state={};graphics.viewport={116,4,408,472,0,1};graphics.state.depthWrite=depth;graphics.state.fog=fog;graphics.data.clear();graphics.submissions.clear();graphics.snapshots.clear();ScreenFade fade;fade.type=kind;fade.alpha=alpha;fade.color=color;fade.draw(renderer);renderer.flush();return graphics.submissions.size()==1&&graphics.data.size()==80;}
API(vertices) const u8* vertices(){return graphics.data.data();}

API(viewport_field) u32 viewport_field(u32 i){const auto& v=graphics.viewport;return i==0?v.x:i==1?v.y:i==2?v.width:v.height;}
API(viewport_depth) float viewport_depth(u32 i){return i?graphics.viewport.far_depth:graphics.viewport.near_depth;}

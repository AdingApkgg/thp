#include "render-fixture.hpp"
#include "../../cpp/game/HudTh14Text.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
struct Glyph {i32 sprite;float x,y;u32 color;bool filtered;};static std::vector<Glyph> glyphs;
static std::vector<AsciiRequest> queued;
void AnmRenderer::set_camera(SceneCamera&,bool){}
int AnmRenderer::draw_ascii_sprite(AnmVm& vm){glyphs.push_back({vm.sprite_index,vm.script_position.x,vm.script_position.y,vm.color,bool(vm.flags&0x80000000u)});return 0;}
API(run) i32 run(i32 high,i32 displayed,i32 alpha,i32 power,i32 continues,i32 life,i32 bombs,i32 points,i32 graze,i32 awards){
    glyphs.clear();AnmResource resource;resource.sprites.resize(400);resource.textures.resize(1);resource.textures[0].width=resource.textures[0].height=256;
    GameEconomy e;e.power=power;e.power_step=40;e.max_power=160;e.life_fragments=life;e.th14_bomb_fragments=bombs;e.point_value=points;e.graze=graze;e.th14_life_awards=awards;
    HudScore score;score.high=high;score.high_continues=8;score.displayed=displayed;score.continues=continues;
    AsciiText output(resource);if(!th14_hud_counters(output,e,score,u8(alpha)))return -1;
    test::RecordingGraphics graphics;AnmRenderer renderer(graphics);SceneCamera full,play;if(!output.draw(renderer,0,full,play))return -2;return glyphs.size();
}
API(word) u32 word(u32 i,u32 k){const auto& g=glyphs[i];return k==0?g.sprite:k==1?g.color:g.filtered;}
API(real) float real(u32 i,u32 k){return k==0?glyphs[i].x:glyphs[i].y;}
API(awards_run) i32 awards_run(i32 result,i32 time,i32 bonus,i32 frames,i32 encoded,i32 alpha){
    glyphs.clear();AnmResource resource;resource.sprites.resize(400);resource.textures.resize(1);resource.textures[0].width=resource.textures[0].height=256;
    AsciiText output(resource);Th14HudAwards data;data.result=result;data.time=time;data.bonus=bonus;data.frames=frames;data.encoded=encoded;data.result_alpha=data.time_alpha=u8(alpha);
    if(!th14_hud_awards(output,data))return -1;queued=output.requests;
    test::RecordingGraphics graphics;AnmRenderer renderer(graphics);SceneCamera full,play;if(!output.draw(renderer,2,full,play))return -2;return glyphs.size();
}
API(request_count) u32 request_count(){return queued.size();}
API(request_byte) u32 request_byte(u32 n,u32 k){return k<queued[n].text.size()?u8(queued[n].text[k]):0;}
API(request_word) u32 request_word(u32 n,u32 k){const auto& r=queued[n];return k==0?r.style.font:k==1?r.style.pass:r.style.color;}

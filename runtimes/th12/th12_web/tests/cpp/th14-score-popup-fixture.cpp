#include "../../cpp/game/ScorePopups.hpp"
#include "../../cpp/game/AsciiText.hpp"
#include "render-fixture.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static ScorePopups popups;static float rate;static AnmResource resource;static AsciiText ascii(resource);
static std::vector<ScoreGlyph> glyphs;static u32 words[18*18];
static std::vector<std::array<u32,5>> bonus_glyphs;
void AnmRenderer::set_camera(SceneCamera&,bool){}
int AnmRenderer::draw_ascii_sprite(AnmVm& vm){
 u32 x,y;std::memcpy(&x,&vm.script_position.x,4);std::memcpy(&y,&vm.script_position.y,4);
 bonus_glyphs.push_back({u32(vm.sprite_index),x,y,vm.color,u32(bool(vm.flags&0x80000000u))});return 0;
}
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
static ScorePopup& entry(u32 n){return n<13?popups.entries[n]:popups.bonuses[n-13];}
API(initialize) void initialize(const u32* data,u32 cursor,float speed){
 rate=speed;popups.cursor=cursor;
 for(u32 n=0;n<18;++n){auto& p=entry(n);std::memcpy(&p,data+18*n,72);p.age.rate=data[18*n+11]?&rate:nullptr;}
}
API(add) void add(u32 bonus,const Vec3* p,i32 value,u32 color,float multiplier){if(bonus)popups.add_bonus(*p,value,color,multiplier,&rate);else popups.add(*p,value,color,&rate);}
API(pool) const u32* pool(){for(u32 n=0;n<18;++n){auto& p=entry(n);std::memcpy(words+18*n,&p,72);words[18*n+11]=p.age.rate!=nullptr;}return words;}
API(cursor) u32 cursor(){return popups.cursor;}
API(tick) void tick(){popups.update(rate);}
API(glyph_count) u32 glyph_count(const Vec3* player){glyphs=popups.glyphs(*player);return glyphs.size();}
API(glyph_word) u32 glyph_word(u32 n,u32 field){const auto& g=glyphs[n];u32 x,y;std::memcpy(&x,&g.x,4);std::memcpy(&y,&g.y,4);const u32 row[]={u32(g.sprite),x,y,g.color};return row[field];}
API(queue) u32 queue(){ascii.clear();if(!popups.queue_bonuses(ascii))return ~0u;return ascii.requests.size();}
API(text) const char* text(u32 n){return ascii.requests[n].text.c_str();}
API(request_word) u32 request_word(u32 n,u32 field){const auto& q=ascii.requests[n];u32 xyz[3];std::memcpy(xyz,&q.position,12);const u32 row[]={xyz[0],xyz[1],xyz[2],q.style.color,u32(q.style.font),u32(q.style.pass),u32(q.style.shadow),u32(q.style.playfield)};return row[field];}
API(bonus_draw) u32 bonus_draw(){
 resource.sprites.resize(400);resource.textures.resize(1);resource.textures[0].width=resource.textures[0].height=256;
 test::RecordingGraphics graphics;AnmRenderer renderer(graphics);SceneCamera full,play;bonus_glyphs.clear();
 return ascii.draw(renderer,2,full,play)?bonus_glyphs.size():~0u;
}
API(bonus_glyph_word) u32 bonus_glyph_word(u32 n,u32 field){return bonus_glyphs[n][field];}

#include "render-fixture.hpp"
#include "../../cpp/game/AsciiText.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
struct Glyph {i32 sprite;float x,y;u32 color;bool filtered;};
static std::vector<Glyph> glyphs;
// Observe the production queue's submission boundary, just like the native
// probe. Sprite binding and all text traversal use the real C++ implementation.
void AnmRenderer::set_camera(SceneCamera&,bool){}
int AnmRenderer::draw_ascii_sprite(AnmVm& vm){
    glyphs.push_back({vm.sprite_index,vm.script_position.x,vm.script_position.y,vm.color,bool(vm.flags&0x80000000u)});return 0;
}
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(run) int run(const char* text,i32 font,float sx,float sy,u32 shadow){
    glyphs.clear();AnmResource resource;resource.sprites.resize(400);resource.textures.resize(1);
    resource.textures[0].width=resource.textures[0].height=256;
    AsciiText output(resource);AsciiStyle style;style.font=font;style.scale={sx,sy};style.shadow=shadow;style.color=0xa5345678;
    if(!output.add(text,{16.25f,28.5f,0},style))return -1;
    test::RecordingGraphics graphics;AnmRenderer renderer(graphics);SceneCamera full,play;
    if(!output.draw(renderer,0,full,play))return -2;
    return glyphs.size();
}
API(word) u32 word(u32 i,u32 k){const auto& g=glyphs[i];return k==0?g.sprite:k==1?g.color:g.filtered;}
API(real) float real(u32 i,u32 k){return k==0?glyphs[i].x:glyphs[i].y;}

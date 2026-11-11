#include "AnmRenderer.hpp"
#include "../runtimes/th12/th12_web/tests/cpp/render-fixture.hpp"
#include "AsciiText.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
struct Glyph {i32 sprite;float x,y,z;u32 color;bool filtered;};
static std::vector<Glyph> glyphs;
// Observe the production queue's submission boundary, just like the native
// probe. Sprite binding and all text traversal use the real C++ implementation.
void AnmRenderer::set_camera(SceneCamera&,bool){}
void AnmRenderer::upload_camera(const SceneCamera&){}
int AnmRenderer::draw_ascii_sprite(AnmVm& vm){
    glyphs.push_back({vm.sprite_index,vm.script_position.x,vm.script_position.y,vm.script_position.z,vm.color,bool(vm.flags&0x80000000u)});return 0;
}
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(run) int run(const char* text,i32 font,float sx,float sy,u32 shadow,u32 width,u32 pass,i32 horizontal,i32 vertical){
    glyphs.clear();AnmResource resource;resource.sprites.resize(400);resource.textures.resize(1);
    resource.textures[0].width=resource.textures[0].height=256;
    AsciiText output(resource);AsciiStyle style;style.font=font;style.scale={sx,sy};style.shadow=shadow;style.color=0xa5345678;style.pass=i32(pass);
#if defined(TH14_ASCII_ALIGNMENT_CANDIDATE)
    style.horizontal=horizontal;style.vertical=vertical;
#endif
    if(!output.add(text,{16.25f,28.5f,-.125f},style))return -1;
    test::RecordingGraphics graphics;AnmRenderer renderer(graphics);SceneCamera full,play;renderer.render_width=width;
    if(!output.draw(renderer,i32(pass),full,play))return -2;
    return glyphs.size();
}
API(word) u32 word(u32 i,u32 k){const auto& g=glyphs[i];return k==0?g.sprite:k==1?g.color:g.filtered;}
API(real) float real(u32 i,u32 k){return k==0?glyphs[i].x:k==1?glyphs[i].y:glyphs[i].z;}

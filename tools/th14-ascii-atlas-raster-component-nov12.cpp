#include "GraphicsDevice.hpp"
#include "AsciiText.hpp"
#include "SceneCompositor.hpp"
#include <cstdlib>
using namespace th11;
namespace { AnmResource resource;std::unique_ptr<sdl::GraphicsDevice> graphics; }
#define API(n) extern "C" __attribute__((export_name(#n)))
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(setup) u32 setup(const u8* bytes,u32 size){
 if(!resource.open(bytes,size))return 0;
 graphics=std::make_unique<sdl::GraphicsDevice>();
 return graphics->initialize()&&graphics->preload(resource);
}
API(run) u32 run(u32 width,u32 height,i32 font,i32 pass){
 auto& g=*graphics;
 if(g.pixels(g.screen)->width!=width){
  g.backend.release(g.screen);g.backend.release(g.depth);
  for(u32 id:{g.screen,g.depth}){auto* p=g.pixels(id);p->width=width;p->height=height;p->pitch=width*(id==g.screen?4:2);if(id==g.screen)p->pixels.resize(size_t(p->pitch)*height);}
 }
 g.initialize_game_pipeline();g.pipeline().fog=false;g.pipeline().depthTest=false;
 AnmManager manager;SceneCompositor compositor(manager);compositor.reset_cameras(true,width,height);
 AnmRenderer renderer(g);renderer.upload_camera(compositor.full_camera);g.clear(0x7f42678b);
 AsciiText text(resource);AsciiStyle style;style.font=font;style.scale={.7f,.3f};style.shadow=true;style.pass=pass;style.color=0xa5345678;
 if(!text.add("A. 1,2s",{16.25f,28.5f,0},style))return 0;
 style.font=(font+1)%6;style.scale={.75f,1.5f};style.shadow=false;style.color=0x803d7fbe;
 if(!text.add("0.9",{620.25f,471.5f,0},style))return 0;
 if(!text.draw(renderer,pass,compositor.full_camera,compositor.play_camera))return 0;
 g.backend.read(g.screen);return 1;
}
API(pixels) const u8* pixels(){return graphics->pixels(graphics->screen)->pixels.data();}
API(pixel_bytes) u32 pixel_bytes(){return graphics->pixels(graphics->screen)->pixels.size();}
API(close) void close(){if(graphics){graphics->unload(resource);graphics.reset();}resource={};}

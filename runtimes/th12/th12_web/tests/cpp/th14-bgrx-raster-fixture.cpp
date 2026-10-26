// Actual production Renderer clear/draw/read with an A8/X8 target selector.
#include "../../../portable/sdl/Renderer.hpp"
#include <emscripten.h>
#include <memory>
#include <cstdlib>
using namespace touhou::sdl;
namespace {
std::unique_ptr<Renderer> renderer;
u8 pixels[16*16*4]{};
PixelFormat format=PixelFormat::Bgra8;
u32 version=0;
Surface resolve_raster(void*,u32 id){return id==1?Surface{1,16,16,format,16*4,pixels,sizeof(pixels),version}:Surface{};}
struct Vertex {float x,y,z,w;u32 color;};
}
extern "C" {
EMSCRIPTEN_KEEPALIVE void* gpu_allocate(u32 n){return std::malloc(n);}
EMSCRIPTEN_KEEPALIVE void gpu_release(void* p){std::free(p);}
EMSCRIPTEN_KEEPALIVE int gpu_initialize(){renderer=std::make_unique<Renderer>(10,resolve_raster,nullptr);return renderer->initialize();}
EMSCRIPTEN_KEEPALIVE int gpu_case(u32 value){
    if(!renderer||(value!=21&&value!=22))return 0;
    renderer->release(1);format=value==21?PixelFormat::Bgra8:PixelFormat::Bgrx8;++version;
    renderer->state=State{};renderer->state.target=1;renderer->state.layout=attributes(VertexLayout::ScreenColor);renderer->viewport({0,0,16,16,0,1});
    auto& p=renderer->pipeline();p.color.operation=p.alpha.operation=ColorOperation::First;
    p.color.first=p.alpha.first={ArgumentSource::Diffuse};return 1;
}
EMSCRIPTEN_KEEPALIVE int gpu_blend(u32 enabled,u32 source,u32 destination,u32 operation,u32 mask){
    if(!renderer||source<1||source>11||destination<1||destination>11||operation<1||operation>5||mask>15)return 0;
    renderer->flush();auto& p=renderer->pipeline();p.blend=enabled!=0;p.sourceBlend=BlendFactor(source-1);p.destinationBlend=BlendFactor(destination-1);p.blendEquation=BlendEquation(operation-1);p.colorMask=mask;return 1;
}
EMSCRIPTEN_KEEPALIVE int gpu_clear(u32 color,const i32* rects,u32 count){if(!renderer)return 0;renderer->clear(1,color,1,0,rects,count);return 1;}
EMSCRIPTEN_KEEPALIVE int gpu_draw(u32 color,float left,float top,float right,float bottom){
    if(!renderer)return 0;const Vertex v[]={{left-.5f,top-.5f,.5f,1,color},{right-.5f,top-.5f,.5f,1,color},{left-.5f,bottom-.5f,.5f,1,color},{right-.5f,bottom-.5f,.5f,1,color}};
    renderer->draw(Topology::Strip,2,v,sizeof(Vertex));return 1;
}
EMSCRIPTEN_KEEPALIVE const u8* gpu_read(){if(!renderer)return nullptr;renderer->read(1);return pixels;}
EMSCRIPTEN_KEEPALIVE void gpu_close(){renderer.reset();}
}

// Actual production Renderer Clear bridge; the test host observes attachments.
#include "../../../portable/sdl/Renderer.hpp"
#include <emscripten.h>
#include <memory>
#include <cstdlib>
#include <cstring>
using namespace touhou::sdl;
namespace {
std::unique_ptr<Renderer> renderer;
u8 pixels[64*48*4]{};
Surface resolve_clear(void*,u32 handle){
    if(handle==1)return {1,64,48,PixelFormat::Bgra8,64*4,pixels,sizeof(pixels),0};
    if(handle==2)return {2,64,48,PixelFormat::Depth24Stencil8,0,nullptr,0,0};
    return {};
}
}
extern "C" {
EMSCRIPTEN_KEEPALIVE void* gpu_allocate(u32 bytes){return std::malloc(bytes);}
EMSCRIPTEN_KEEPALIVE void gpu_release(void* pointer){std::free(pointer);}
EMSCRIPTEN_KEEPALIVE int gpu_initialize(){
    renderer=std::make_unique<Renderer>(10,resolve_clear,nullptr);
    if(!renderer->initialize())return 0;
    renderer->state.target=1;renderer->state.depth=2;renderer->viewport({0,0,64,48,0,1});
    return 1;
}
EMSCRIPTEN_KEEPALIVE int gpu_clear(u32 flags,u32 color,u32 depth,u32 stencil,const i32* rects,u32 count){
    if(!renderer)return 0;
    float value;std::memcpy(&value,&depth,4);renderer->clear(flags,color,value,stencil,rects,count);return 1;
}
EMSCRIPTEN_KEEPALIVE u8* gpu_read(){if(!renderer)return nullptr;renderer->read(1);return pixels;}
EMSCRIPTEN_KEEPALIVE void gpu_close(){renderer.reset();}
}

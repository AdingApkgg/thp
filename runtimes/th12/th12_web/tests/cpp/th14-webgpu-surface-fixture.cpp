#include "../../../portable/sdl/Renderer.hpp"
#include <emscripten.h>
#include <cstdlib>
#include <map>
#include <memory>
using namespace touhou::sdl;
namespace {
std::map<u32,Surface> surfaces;
std::unique_ptr<Renderer> renderer;
Surface resolve_fixture(void*,u32 id){auto it=surfaces.find(id);return it==surfaces.end()?Surface{}:it->second;}
}
extern "C" {
EMSCRIPTEN_KEEPALIVE void* gpu_allocate(u32 size){return std::malloc(size);}
EMSCRIPTEN_KEEPALIVE void gpu_release(void* pointer){std::free(pointer);}
EMSCRIPTEN_KEEPALIVE int gpu_initialize(){renderer=std::make_unique<Renderer>(10,resolve_fixture,nullptr);return renderer->initialize();}
EMSCRIPTEN_KEEPALIVE int gpu_surface(u32 id,u32 width,u32 height,u32 format,u32 pitch,u8* data,u32 size){if(!id||format>u32(PixelFormat::Depth24Stencil8))return 0;renderer->release(id);surfaces[id]={id,width,height,PixelFormat(format),pitch,data,size,0};renderer->prepare(id);return 1;}
EMSCRIPTEN_KEEPALIVE int gpu_resample(u32 source,const i32* from,u32 target,const i32* to,const float* weights,u32 width,u32 height){return renderer->resample(source,from,target,to,weights,width,height);}
EMSCRIPTEN_KEEPALIVE const u8* gpu_read(u32 id){renderer->read(id);return surfaces.at(id).data;}
EMSCRIPTEN_KEEPALIVE void gpu_copy(u32 source,const i32* rect,u32 target,const i32* point){renderer->copy(source,rect,target,point);}
EMSCRIPTEN_KEEPALIVE void gpu_clear(u32 id,u32 color,const i32* rects,u32 count){renderer->state.target=id;renderer->state.depth=0;const auto s=surfaces.at(id);renderer->viewport({0,0,s.width,s.height,0,1});renderer->clear(1,color,1,0,rects,count);}
EMSCRIPTEN_KEEPALIVE void gpu_dirty(u32 id){renderer->flush();++surfaces.at(id).version;}
EMSCRIPTEN_KEEPALIVE void gpu_present(u32 id){renderer->present(id);}
}

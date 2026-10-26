#include "../../../portable/sdl/Renderer.hpp"
#include "Th14WebGpuCallbacks.hpp"
#include <emscripten.h>
#include <memory>
using namespace touhou::sdl;
namespace {
std::unique_ptr<Renderer> renderer;
u8 pixels[16]{};
volatile u32 status[12]{};
Surface resolve_fixture(void*,u32 id){return id==1?Surface{1,2,2,PixelFormat::Bgra8,8,pixels,16,0}:Surface{};}
void first(void* data){
    volatile u32 guard[2048];for(u32 i=0;i<2048;++i)guard[i]=i^0x81726354u;
    status[0]=1;status[1]=u32(std::uintptr_t(data));
    renderer->clear(1,0xff123456,1,0);renderer->read(1);
    for(u32 i=0;i<2048;++i)if(guard[i]!=(i^0x81726354u))++status[7];
    for(u32 i=0;i<16;++i)if(pixels[i]!=(i%4==0?0x56:i%4==1?0x34:i%4==2?0x12:0xff))++status[8];
    status[2]=1;status[0]=2;
}
void second(void* data){if(status[0]!=2)++status[9];status[3]=u32(std::uintptr_t(data));status[0]=3;}
EM_BOOL frame(double time,void* data){if(status[0]<3)++status[9];++status[4];status[5]=u32(time);status[6]=u32(std::uintptr_t(data));return status[4]<3;}
}
extern "C" {
EMSCRIPTEN_KEEPALIVE int gpu_initialize(){renderer=std::make_unique<Renderer>(10,resolve_fixture,nullptr);if(!renderer->initialize())return 0;renderer->state.target=1;renderer->viewport({0,0,2,2,0,1});return 1;}
EMSCRIPTEN_KEEPALIVE const volatile u32* gpu_status(){return status;}
EMSCRIPTEN_KEEPALIVE void gpu_start(){th14_webgpu_schedule(first,reinterpret_cast<void*>(7),0);th14_webgpu_schedule(second,reinterpret_cast<void*>(11),0);th14_webgpu_request_frames(frame,reinterpret_cast<void*>(13));}
EMSCRIPTEN_KEEPALIVE void th11_key(unsigned scan,unsigned down){if(status[0]!=2)++status[9];status[10]=scan;status[11]=down;}
}

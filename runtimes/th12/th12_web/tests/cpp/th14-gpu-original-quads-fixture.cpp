// Production ANM geometry and production SDL renderer, with a diagnostic texture.
#include "th14-render-fixture.cpp"
#include "th14-gpu-original-quads-data.hpp"
#include "../../../portable/sdl/Renderer.hpp"
#include <emscripten.h>
#include <memory>
namespace original_quad_gpu {
using namespace touhou::sdl;
static u8 target_pixels[640*480*4]{},cropped_pixels[640*480*4]{};
static u32 texture_pixels[16]{};
static std::unique_ptr<Renderer> renderer;
static u32 last_status=0,last_draw_count=0;
static Surface resolve_surface(void*,u32 id){
    if(id==1)return {1,640,480,PixelFormat::Bgra8,2560,target_pixels,sizeof(target_pixels),0};
    if(id==2)return {2,4,4,PixelFormat::Bgra8,16,reinterpret_cast<u8*>(texture_pixels),sizeof(texture_pixels),0};
    return {};
}
}
extern "C" {
EMSCRIPTEN_KEEPALIVE int gpu_initialize(){
    using namespace original_quad_gpu;
    for(u32 i=0;i<16;++i)texture_pixels[i]=((47+i*53)%256)<<24|((31+i*73)%256)<<16|((19+i*41)%256)<<8|((11+i*97)%256);
    renderer=std::make_unique<touhou::sdl::Renderer>(10,resolve_surface,nullptr);
    return renderer->initialize();
}
EMSCRIPTEN_KEEPALIVE const char* gpu_error(){return original_quad_gpu::renderer?original_quad_gpu::renderer->error():"renderer not initialized";}
EMSCRIPTEN_KEEPALIVE u32 gpu_status(){return original_quad_gpu::last_status;}
EMSCRIPTEN_KEEPALIVE u32 gpu_draw_count(){return original_quad_gpu::last_draw_count;}
EMSCRIPTEN_KEEPALIVE const u8* gpu_original_quad_case(u32 index){
    using namespace original_quad_gpu;
    if(!renderer||index>=sizeof(original_quad_cases)/sizeof(original_quad_cases[0]))return nullptr;
    const auto& c=original_quad_cases[index];
    fixture.graphics.state=PipelineState{};fixture.graphics.configure_game(1);
    last_status=quad_case(c.mode,c.colorMode,c.relation,c.tinted,c.visibility,c.sample);
    last_draw_count=fixture.graphics.submissions.size();
    auto& r=*renderer;r.state=touhou::sdl::State{};r.state.target=1;r.state.texture=2;
    r.state.viewport={0,0,640,480,0,1};r.state.layout=attributes(VertexLayout::ScreenColorUv);
    r.pipeline()=fixture.graphics.state;
    // Both devices use the same controlled non-fog screen-space pipeline.
    r.pipeline().depthTest=false;r.pipeline().fog=false;
    r.clear(1,0xff42678b,1,0);
    for(const auto& s:fixture.graphics.submissions){
        if(s.topology!=u32(Topology::Triangles))return nullptr;
        r.draw_batch(s.count,fixture.graphics.data.data()+s.start,s.stride);
    }
    r.read(1);
    const auto* crop=c.crop;
    for(u32 y=0;y<crop[3];++y)std::memcpy(cropped_pixels+y*crop[2]*4,target_pixels+((crop[1]+y)*640+crop[0])*4,crop[2]*4);
    return cropped_pixels;
}
}

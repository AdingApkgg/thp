#include "th14-render-fixture.cpp"
#include "th14-gpu-original-shapes-data.hpp"
#include "../../../portable/sdl/Renderer.hpp"
#include <emscripten.h>
#include <memory>
namespace original_shape_gpu {
using namespace touhou::sdl;
static u8 target_pixels[640*480*16]{},cropped_pixels[640*480*16]{};
static std::unique_ptr<Renderer> renderer;
static u32 last_status=0,last_draw_count=0;
static Surface resolve_surface(void*,u32 id){
    if(id==1)return {1,640,480,PixelFormat::Bgra8,10240,target_pixels,sizeof(target_pixels),0};
    return {};
}
}
extern "C" {
EMSCRIPTEN_KEEPALIVE int gpu_initialize(){
    using namespace original_shape_gpu;
    renderer=std::make_unique<touhou::sdl::Renderer>(10,resolve_surface,nullptr);
    return renderer->initialize();
}
EMSCRIPTEN_KEEPALIVE const char* gpu_error(){return original_shape_gpu::renderer?original_shape_gpu::renderer->error():"renderer not initialized";}
EMSCRIPTEN_KEEPALIVE u32 gpu_status(){return original_shape_gpu::last_status;}
EMSCRIPTEN_KEEPALIVE u32 gpu_draw_count(){return original_shape_gpu::last_draw_count;}
EMSCRIPTEN_KEEPALIVE const u8* gpu_original_shape_case(u32 index){
    using namespace original_shape_gpu;
    if(!renderer||index>=sizeof(original_shape_cases)/sizeof(original_shape_cases[0]))return nullptr;
    const auto& c=original_shape_cases[index];
    fixture.graphics.state=PipelineState{};fixture.graphics.configure_game(1);
    last_status=shape_case(c.mode,c.anchor,c.parent,c.resolution);
    last_draw_count=fixture.graphics.submissions.size();
    auto& r=*renderer;r.state=touhou::sdl::State{};r.state.target=1;
    r.state.viewport={0,0,640,480,0,1};r.state.layout=attributes(VertexLayout::ScreenColor);
    r.pipeline()=fixture.graphics.state;r.pipeline().blend=false;r.pipeline().depthTest=false;r.pipeline().fog=false;
    r.pipeline().color.operation=r.pipeline().alpha.operation=ColorOperation::First;
    r.pipeline().color.first=r.pipeline().alpha.first={ArgumentSource::Diffuse};
    r.clear(1,0xff42678b,1,0);
    for(const auto& s:fixture.graphics.submissions)r.draw(Topology(s.topology),s.count,fixture.graphics.data.data()+s.start,s.stride);
    r.read(1);const auto* crop=c.crop;
    for(u32 y=0;y<crop[3];++y)std::memcpy(cropped_pixels+y*crop[2]*16,target_pixels+((crop[1]+y)*640+crop[0])*16,crop[2]*16);
    return cropped_pixels;
}
}

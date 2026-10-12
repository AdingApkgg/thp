#include "th14-gpu-original-shapes-fixture.cpp"
#include "th14-gpu-original-shapes-input-data.hpp"
extern "C" EMSCRIPTEN_KEEPALIVE const u8* gpu_recorded_shape_case(u32 index){
    using namespace original_shape_gpu;
    if(!renderer||index>=sizeof(native_shape_cases)/sizeof(native_shape_cases[0]))return nullptr;
    const auto& c=native_shape_cases[index];const auto* crop=original_shape_cases[index].crop;
    last_status=0;last_draw_count=c.count;
    auto& r=*renderer;r.state=touhou::sdl::State{};r.state.target=1;
    r.state.viewport={0,0,640,480,0,1};r.state.layout=attributes(VertexLayout::ScreenColor);
    r.configure_game(1);auto& p=r.pipeline();p.depthTest=false;p.depthWrite=false;p.fog=false;
    p.color.operation=p.alpha.operation=ColorOperation::First;
    p.color.first=p.alpha.first={ArgumentSource::Diffuse};
    r.clear(1,0xff42678b,1,0);
    for(u32 i=0;i<c.count;++i){const auto& d=native_shape_draws[c.start+i];r.draw(Topology(d.topology),d.count,native_shape_words+d.offset,20);}
    r.read(1);
    for(u32 y=0;y<crop[3];++y)std::memcpy(cropped_pixels+y*crop[2]*4,target_pixels+((crop[1]+y)*640+crop[0])*4,crop[2]*4);
    return cropped_pixels;
}

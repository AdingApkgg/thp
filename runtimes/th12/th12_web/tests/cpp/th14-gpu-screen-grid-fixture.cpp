#include "th14-gpu-original-shapes-fixture.cpp"
#include "th14-gpu-screen-grid-data.hpp"
extern "C" EMSCRIPTEN_KEEPALIVE const u8* gpu_screen_grid_case(u32 index){
    using namespace original_shape_gpu;
    if(!renderer||index>=sizeof(grid_cases)/sizeof(grid_cases[0]))return nullptr;
    const auto& c=grid_cases[index];last_status=0;last_draw_count=c.count;
    auto& r=*renderer;r.state=touhou::sdl::State{};r.state.target=1;
    r.state.viewport={0,0,640,480,0,1};r.state.layout=attributes(VertexLayout::ScreenColor);
    r.configure_game(1);auto& p=r.pipeline();p.depthTest=false;p.depthWrite=false;p.fog=false;
    p.color.operation=p.alpha.operation=ColorOperation::First;p.color.first=p.alpha.first={ArgumentSource::Diffuse};
    r.clear(1,0xff42678b,1,0);
    for(u32 i=0;i<c.count;++i){const auto& d=grid_draws[c.start+i];r.draw(Topology(d.topology),d.count,grid_words+d.offset,20);}
    r.read(1);
    for(u32 y=0;y<c.height;++y)std::memcpy(cropped_pixels+y*c.width*4,target_pixels+((c.top+y)*640+c.left)*4,c.width*4);
    return cropped_pixels;
}

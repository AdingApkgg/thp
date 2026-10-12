#include "../../../portable/sdl/Renderer.hpp"
#include <emscripten.h>
#include <cstring>
#include <memory>
using namespace touhou::sdl;
namespace {
u8 target_pixels[32*32*4]{};
u32 texture_pixels[16]{};
Surface resolve_fixture(void*,u32 id){
    if(id==1)return {1,32,32,PixelFormat::Bgra8,128,target_pixels,sizeof(target_pixels),0};
    if(id==2)return {2,4,4,PixelFormat::Bgra8,16,reinterpret_cast<u8*>(texture_pixels),sizeof(texture_pixels),0};
    return {};
}
std::unique_ptr<Renderer> renderer;
struct Vertex {float x,y,z,rhw;u32 color;float u,v;};
}
extern "C" {
EMSCRIPTEN_KEEPALIVE int gpu_initialize(){
    for(u32 i=0;i<16;++i)texture_pixels[i]=((47+i*53)%256)<<24|((31+i*73)%256)<<16|((19+i*41)%256)<<8|((11+i*97)%256);
    renderer=std::make_unique<Renderer>(10,resolve_fixture,nullptr);
    return renderer->initialize();
}
EMSCRIPTEN_KEEPALIVE const char* gpu_error(){return renderer?renderer->error():"renderer not initialized";}
EMSCRIPTEN_KEEPALIVE const u8* gpu_case(u32 source,u32 destination,u32 equation,u32 point,u32 address,u32 offset){
    if(!renderer||source<1||source>11||destination<1||destination>11||equation<1||equation>5||address>2)return nullptr;
    auto& r=*renderer;r.state=State{};r.state.target=1;r.state.texture=2;
    r.state.viewport={0,0,32,32,0,1};r.state.layout=attributes(VertexLayout::ScreenColorUv);
    auto& p=r.pipeline();p.depthWrite=false;p.blend=true;
    p.sourceBlend=BlendFactor(source-1);p.destinationBlend=BlendFactor(destination-1);p.blendEquation=BlendEquation(equation-1);
    p.color.operation=p.alpha.operation=ColorOperation::Multiply;
    p.alpha.first=p.color.first={ArgumentSource::Texture};p.alpha.second=p.color.second={ArgumentSource::Diffuse};
    p.minFilter=p.magFilter=point?Filter::Nearest:Filter::Linear;
    p.addressU=p.addressV=address==0?Address::Repeat:address==1?Address::Clamp:Address::Mirror;
    r.clear(1,0xff42678b,1,0);const float d=offset*.25f;
    const Vertex v[]={{3.5f+d,4.5f+d,0,1,0xc8b56e29,-.25f,-.125f},
        {25.5f+d,4.5f+d,0,1,0x795ac4e8,1.25f,-.125f},
        {3.5f+d,26.5f+d,0,1,0xea28cf7b,-.25f,1.125f},
        {25.5f+d,26.5f+d,0,1,0x467c318e,1.25f,1.125f}};
    r.draw(Topology::Strip,2,v,sizeof(Vertex));r.read(1);return target_pixels;
}
}

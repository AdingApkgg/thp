#define resolve_fixture resolve_base_fixture
#include "th14-gpu-raster-fixture.cpp"
#undef resolve_fixture
#include <cmath>
namespace {
Surface resolve_depth_fixture(void* owner,u32 id){
    if(id==3||id==4)return {id,32,32,id==3?PixelFormat::Depth16:PixelFormat::Depth24Stencil8,0,nullptr,0,0};
    return resolve_base_fixture(owner,id);
}
}
extern "C" EMSCRIPTEN_KEEPALIVE int gpu_depth_initialize(){
    for(u32 i=0;i<16;++i)texture_pixels[i]=((47+i*53)%256)<<24|((31+i*73)%256)<<16|((19+i*41)%256)<<8|((11+i*97)%256);
    renderer=std::make_unique<Renderer>(10,resolve_depth_fixture,nullptr);return renderer->initialize();
}
extern "C" EMSCRIPTEN_KEEPALIVE const u8* gpu_alpha_depth_case(u32 format,u32 compare,u32 write,u32 depth,u32 reference,u32 low,u32 point){
    if(!renderer||format>1||compare<1||compare>8||write>1||depth>4||reference>255||low>1||point>1)return nullptr;
    auto& r=*renderer;static u32 previousLow=2;
    if(low!=previousLow){r.release(2);previousLow=low;for(u32 i=0;i<16;++i)texture_pixels[i]=(low?i%4:(47+i*53)%256)<<24|((31+i*73)%256)<<16|((19+i*41)%256)<<8|((11+i*97)%256);}
    r.state=State{};r.state.target=1;r.state.depth=format?4:3;r.state.texture=2;
    r.state.viewport={0,0,32,32,0,1};r.state.layout=attributes(VertexLayout::ScreenColorUv);
    auto& p=r.pipeline();p.depthTest=true;p.depthWrite=write;p.depthCompare=Compare(compare-1);
    p.blend=true;p.sourceBlend=BlendFactor::SourceAlpha;p.destinationBlend=BlendFactor::InverseSourceAlpha;
    p.alphaTest=true;p.alphaCompare=Compare::GreaterEqual;p.alphaReference=reference;
    p.color.operation=p.alpha.operation=ColorOperation::Multiply;
    p.alpha.first=p.color.first={ArgumentSource::Texture};p.alpha.second=p.color.second={ArgumentSource::Diffuse};
    p.minFilter=p.magFilter=point?Filter::Nearest:Filter::Linear;p.addressU=p.addressV=Address::Clamp;
    r.clear(3,0xff42678b,.75f,0);
    const float zs[]={.25f,.6f,std::nextafter(.6f,0.f),std::nextafter(.6f,1.f),.75f},z=zs[depth];
    const Vertex front[]={{3.5f,4.5f,z,1,0xc8b56e29,-.25f,-.125f},{25.5f,4.5f,z,1,0x795ac4e8,1.25f,-.125f},
        {3.5f,26.5f,z,1,0xea28cf7b,-.25f,1.125f},{25.5f,26.5f,z,1,0x467c318e,1.25f,1.125f}};
    r.draw(Topology::Strip,2,front,sizeof(Vertex));
    // Draw after the alpha-tested foreground. Only surviving foreground
    // fragments which wrote closer depth may hide this opaque second layer.
    r.state.texture=0;p.blend=false;p.alphaTest=false;p.depthWrite=false;p.depthCompare=Compare::LessEqual;
    const Vertex back[]={{-.5f,-.5f,.6f,1,0xffdda336,0,0},{31.5f,-.5f,.6f,1,0xffdda336,0,0},
        {-.5f,31.5f,.6f,1,0xffdda336,0,0},{31.5f,31.5f,.6f,1,0xffdda336,0,0}};
    r.draw(Topology::Strip,2,back,sizeof(Vertex));r.read(1);return target_pixels;
}

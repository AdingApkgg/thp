#include "../../cpp/game/TextRaster.hpp"
#include "th14-gpu-text-data.hpp"
#include "../../../portable/sdl/Renderer.hpp"
#include <emscripten.h>
#include <cstdlib>
#include <memory>
using namespace th11;
namespace text_gpu {
static TextRaster raster;
static TextureImage image;
static u8 target[640*96*4],cropped[520*40*4];
static std::unique_ptr<touhou::sdl::Renderer> renderer;
static u32 generation=0;
static touhou::sdl::Surface resolve_surface(void*,u32 id){
 if(id==1)return {1,640,96,touhou::graphics::PixelFormat::Bgra8,2560,target,sizeof(target),0};
 if(id==2)return {2,image.width,image.height,image.format,image.pitch,image.pixels.data(),u32(image.pixels.size()),generation};
 return {};
}
struct Vertex {float x,y,z,w;u32 color;float u,v;};
}
extern "C" {
EMSCRIPTEN_KEEPALIVE void* gpu_allocate(u32 size){return std::malloc(size);}
EMSCRIPTEN_KEEPALIVE void gpu_release(void* p){std::free(p);}
EMSCRIPTEN_KEEPALIVE u32 gpu_load(u32 slot,const u8* data,u32 size){return text_gpu::raster.glyphs.load(slot,data,size);}
EMSCRIPTEN_KEEPALIVE int gpu_initialize(){text_gpu::renderer=std::make_unique<touhou::sdl::Renderer>(10,text_gpu::resolve_surface,nullptr);return text_gpu::renderer->initialize();}
EMSCRIPTEN_KEEPALIVE const u8* gpu_upload_pixels(){return text_gpu::image.pixels.data();}
EMSCRIPTEN_KEEPALIVE const u8* gpu_scratch_pixels(){return text_gpu::raster.scratch.pixels.data();}
EMSCRIPTEN_KEEPALIVE const u8* gpu_text_case(u32 index){
 using namespace text_gpu;using namespace touhou::graphics;
 if(!renderer||index>=640)return nullptr;
 const u32 text_index=index/8,format=(index/4)%2,filter=(index/2)%2,scaling=index%2;const auto& c=text_gpu_inputs[text_index];
 renderer->release(2);image.width=520;image.height=40;image.pitch=520*(format?4:2);image.format=format?PixelFormat::Bgra8:PixelFormat::Argb4444;image.pixels.assign(image.pitch*image.height,0xa5);++generation;
 if(!raster.write(image,{0,0,512,32},c.text,{c.offset,c.height,c.font,c.color,c.outline,c.spacing,c.plain!=0}))return nullptr;
 auto& r=*renderer;r.state=touhou::sdl::State{};r.state.target=1;r.state.texture=2;r.state.viewport={0,0,640,96,0,1};r.state.layout=attributes(VertexLayout::ScreenColorUv);
 auto& p=r.pipeline();p.blend=true;p.sourceBlend=BlendFactor::SourceAlpha;p.destinationBlend=BlendFactor::InverseSourceAlpha;p.alphaTest=true;p.alphaReference=1;p.alphaCompare=Compare::GreaterEqual;p.color.operation=p.alpha.operation=ColorOperation::Multiply;p.color.first=p.alpha.first={ArgumentSource::Texture};p.color.second=p.alpha.second={ArgumentSource::Diffuse};p.minFilter=p.magFilter=filter?Filter::Linear:Filter::Nearest;p.addressU=p.addressV=Address::Clamp;
 const float scale=scaling?.5f:1.f,left=scaling?4.375f:4.f,top=scaling?3.375f:3.f,width=512*scale,height=32*scale,u=512.f/520.f,v=32.f/40.f;
 const Vertex vertices[]={{left,top,0,1,0xffffffff,0,0},{left+width,top,0,1,0xffffffff,u,0},{left,top+height,0,1,0xffffffff,0,v},{left+width,top+height,0,1,0xffffffff,u,v}};
 r.clear(1,0xff42678b,1,0);r.draw(Topology::Strip,2,vertices,sizeof(Vertex));r.read(1);
 const u32 w=scaling?264:520,h=scaling?24:40;for(u32 y=0;y<h;++y)std::memcpy(cropped+y*w*4,target+y*640*4,w*4);return cropped;
}
}

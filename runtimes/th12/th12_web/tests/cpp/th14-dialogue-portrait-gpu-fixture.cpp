#include "th14-dialogue-portrait-geometry-fixture.cpp"
#include "../../cpp/game/TextureImage.hpp"
#include "../../../portable/sdl/Renderer.hpp"
#include <emscripten.h>
#include <memory>
namespace portrait_gpu {
using namespace touhou::sdl;
static u8 target_pixels[640*480*4]{},crop_pixels[640*480*4]{};
static std::vector<TextureImage> images;static std::unique_ptr<Renderer> renderer;
static Surface resolve_surface(void*,u32 id){if(id==1)return {1,640,480,PixelFormat::Bgra8,2560,target_pixels,sizeof target_pixels,0};if(id>=10&&id-10<images.size()){auto& t=images[id-10];return {id,t.width,t.height,t.format,t.pitch,t.pixels.data(),u32(t.pixels.size()),0};}return {};}
}
extern "C" {
EMSCRIPTEN_KEEPALIVE i32 gpu_initialize(){using namespace portrait_gpu;renderer=std::make_unique<touhou::sdl::Renderer>(10,resolve_surface,nullptr);return renderer->initialize();}
EMSCRIPTEN_KEEPALIVE const char* gpu_error(){return portrait_gpu::renderer?portrait_gpu::renderer->error():"renderer not initialized";}
EMSCRIPTEN_KEEPALIVE i32 portrait_gpu_begin(u32 index,float rate,i32 immediate){using namespace portrait_gpu;if(!renderer)return 0;for(u32 i=0;i<images.size();++i)renderer->release(i+10);images.clear();if(!begin_geometry(index,rate,immediate))return 0;for(auto& texture:resource.textures){TextureImage image;if(!image.load(texture))return 0;images.push_back(std::move(image));}return 1;}
EMSCRIPTEN_KEEPALIVE i32 portrait_gpu_step(i32 label){if(label>=0)sprite_interrupt(label);return geometry_step();}
EMSCRIPTEN_KEEPALIVE const u8* portrait_gpu_frame(u32 left,u32 top,u32 width,u32 height){using namespace portrait_gpu;if(!renderer||!width||!height||left+width>640||top+height>480)return nullptr;auto& r=*renderer;r.state=touhou::sdl::State{};r.state.target=1;r.state.viewport={0,0,640,480,0,1};r.state.layout=attributes(VertexLayout::ScreenColorUv);r.configure_game(1);r.pipeline().depthTest=false;r.pipeline().fog=false;r.pipeline().textureTransform=false;r.pipeline().color.second=r.pipeline().alpha.second={ArgumentSource::Diffuse};r.clear(1,0xff42678b,1,0);
 for(u32 i=0;i<geometry_count();++i){const auto* m=portrait_graphics.materials.data()+i*9;r.state.texture=m[0]+9;auto& p=r.pipeline();p.depthWrite=m[1];p.sourceBlend=BlendFactor(m[2]-1);p.destinationBlend=BlendFactor(m[3]-1);p.blendEquation=BlendEquation(m[4]-1);p.minFilter=m[5]==1?Filter::Nearest:Filter::Linear;p.magFilter=m[6]==1?Filter::Nearest:Filter::Linear;p.addressU=m[7]==1?Address::Repeat:m[7]==2?Address::Mirror:Address::Clamp;p.addressV=m[8]==1?Address::Repeat:m[8]==2?Address::Mirror:Address::Clamp;u32 triangles[42];const auto* vertices=portrait_graphics.quads.data()+i*28;u32 at=0;for(u32 vertex:{0,1,2,1,2,3})for(u32 f=0;f<7;++f)triangles[at++]=vertices[vertex*7+f];r.draw_batch(2,triangles,28);}
 r.read(1);for(u32 y=0;y<height;++y)std::memcpy(crop_pixels+y*width*4,target_pixels+((top+y)*640+left)*4,width*4);return crop_pixels;}
EMSCRIPTEN_KEEPALIVE u32 portrait_gpu_quads(){return geometry_count();}
}

#include "../../cpp/sdl/FontDevice.hpp"
#include "th14-font-alignment-gpu-data.hpp"
#include <emscripten.h>
#include <memory>
using namespace th11;
namespace font_device_gpu {
static std::unique_ptr<sdl::GraphicsDevice> graphics;
static std::unique_ptr<sdl::FontDevice> font;
static AnmResource resources[2];
static AnmSprite sprite;
static u32 handles[2],last_handle=0,routes=0;
static u8 cropped[520*40*4];
struct Vertex {float x,y,z,w;u32 color;float u,v;};
}
extern "C" {
EMSCRIPTEN_KEEPALIVE int gpu_initialize(){
 using namespace font_device_gpu;
 graphics=std::make_unique<sdl::GraphicsDevice>();if(!graphics->initialize())return 0;font=std::make_unique<sdl::FontDevice>(*graphics);
 AnmVm vm{};DialogueText request;request.bytes="Text";
 if(!font->text(vm,request)&&!font->waiting&&font->writes==0)routes|=1;
 FontBitmapTh14 bitmap;bitmap.format=21;if(!font->initialize(&bitmap))routes|=2;bitmap.format=26;if(!font->initialize(&bitmap))return 0;
 for(u32 format=0;format<2;++format){auto& resource=resources[format];AnmTexture texture;texture.kind=AnmTexture::Kind::Blank;texture.width=520;texture.height=40;texture.format=format?1:5;resource.textures.push_back(texture);if(!graphics->preload(resource))return 0;handles[format]=graphics->texture(resource,0);auto* image=graphics->pixels(handles[format]);if(!image)return 0;std::fill(image->pixels.begin(),image->pixels.end(),0xa5);graphics->changed(handles[format]);}
 vm.resource=&resources[0];if(!font->text(vm,request)&&font->waiting&&font->writes==0)routes|=4;
 vm.resource=nullptr;if(!font->text(vm,request)&&!font->waiting&&font->writes==0)routes|=8;
 sprite.texture=0;sprite.width=512;sprite.height=32;AnmResource missing;vm.resource=&missing;vm.sprite=&sprite;if(!font->text(vm,request)&&!font->waiting&&font->writes==0)routes|=16;
 return routes==31;
}
EMSCRIPTEN_KEEPALIVE u32 gpu_waiting_routes(){return font_device_gpu::routes;}
EMSCRIPTEN_KEEPALIVE u32 gpu_writes(){return font_device_gpu::font?font_device_gpu::font->writes:0;}
EMSCRIPTEN_KEEPALIVE const char* gpu_error(){return font_device_gpu::font?font_device_gpu::font->error.c_str():"font unavailable";}
EMSCRIPTEN_KEEPALIVE const u8* gpu_upload_pixels(){using namespace font_device_gpu;auto* image=graphics->pixels(last_handle);return image?image->pixels.data():nullptr;}
EMSCRIPTEN_KEEPALIVE const u8* gpu_text_case(u32 index){
 using namespace font_device_gpu;using namespace touhou::graphics;if(!graphics||index>=1920)return nullptr;
 const u32 text_index=index/8,format=(index/4)%2,filter=(index/2)%2,scaling=index%2;const auto& c=text_gpu_inputs[text_index];
 AnmVm vm{};vm.resource=&resources[format];vm.sprite=&sprite;vm.rectangle_columns=c.height;vm.flags2=c.plain?0x800:0;
 DialogueText request;request.color=c.color;request.offset=c.offset;request.font=c.spacing/2;request.style=c.font;request.bytes=c.text;request.right_aligned=c.alignment==1;request.centered=c.alignment==2;
 if(!font->text(vm,request)||font->waiting||!(vm.flags&1))return nullptr;last_handle=handles[format];
 auto& r=graphics->backend;r.state=touhou::sdl::State{};r.state.target=sdl::GraphicsDevice::screen;r.state.texture=last_handle;r.state.viewport={0,0,640,96,0,1};r.state.layout=attributes(VertexLayout::ScreenColorUv);
 auto& p=r.pipeline();p.blend=true;p.sourceBlend=BlendFactor::SourceAlpha;p.destinationBlend=BlendFactor::InverseSourceAlpha;p.alphaTest=true;p.alphaReference=1;p.alphaCompare=Compare::GreaterEqual;p.color.operation=p.alpha.operation=ColorOperation::Multiply;p.color.first=p.alpha.first={ArgumentSource::Texture};p.color.second=p.alpha.second={ArgumentSource::Diffuse};p.minFilter=p.magFilter=filter?Filter::Linear:Filter::Nearest;p.addressU=p.addressV=Address::Clamp;
 const float scale=scaling?.5f:1.f,left=scaling?4.375f:4.f,top=scaling?3.375f:3.f,width=512*scale,height=32*scale,u=512.f/520.f,v=32.f/40.f;
 const Vertex vertices[]={{left,top,0,1,0xffffffff,0,0},{left+width,top,0,1,0xffffffff,u,0},{left,top+height,0,1,0xffffffff,0,v},{left+width,top+height,0,1,0xffffffff,u,v}};
 r.clear(1,0xff42678b,1,0);r.draw(Topology::Strip,2,vertices,sizeof(Vertex));r.read(sdl::GraphicsDevice::screen);const auto* target=graphics->pixels(sdl::GraphicsDevice::screen);
 const u32 w=scaling?264:520,h=scaling?24:40;for(u32 y=0;y<h;++y)std::memcpy(cropped+y*w*4,target->pixels.data()+y*target->pitch,w*4);return cropped;
}
}

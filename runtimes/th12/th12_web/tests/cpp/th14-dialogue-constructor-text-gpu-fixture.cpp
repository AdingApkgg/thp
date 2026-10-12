#include "th14-dialogue-constructor-geometry-fixture.cpp"
#include "../../cpp/sdl/FontDevice.hpp"
#include <emscripten.h>
namespace constructor_text_gpu {
static std::unique_ptr<sdl::GraphicsDevice> graphics;
static std::unique_ptr<sdl::FontDevice> font;
static u8 cropped[640*480*4];
}
extern "C" {
EMSCRIPTEN_KEEPALIVE i32 gpu_initialize(){using namespace constructor_text_gpu;graphics=std::make_unique<sdl::GraphicsDevice>();if(!graphics->initialize())return 0;font=std::make_unique<sdl::FontDevice>(*graphics);FontBitmapTh14 bitmap;return font->initialize(&bitmap);}
EMSCRIPTEN_KEEPALIVE const char* gpu_error(){return constructor_text_gpu::font?constructor_text_gpu::font->error.c_str():"font unavailable";}
EMSCRIPTEN_KEEPALIVE i32 text_gpu_begin(){using namespace constructor_text_gpu;if(!graphics)return 0;graphics->unload(resource);if(!begin_constructor_geometry(1,0))return 0;return graphics->preload(resource);}
EMSCRIPTEN_KEEPALIVE const u8* text_gpu_write(u32 line,i32 font_index,i32 alignment,u32 color,i32 offset,i32 spacing,const char* bytes){using namespace constructor_text_gpu;if(line>=vms.size())return nullptr;DialogueText request;request.bytes=bytes;request.color=color;request.offset=offset;request.font=spacing/2;request.style=font_index;request.right_aligned=alignment==1;request.centered=alignment==2;if(!font->text(*vms[line],request)||font->waiting)return nullptr;capture_lifecycle();capture_sprite();const auto handle=graphics->texture(resource,vms[line]->sprite->texture);auto* image=graphics->pixels(handle);if(!image||image->pixels.size()!=1024*1024*2)return nullptr;return image->pixels.data();}
EMSCRIPTEN_KEEPALIVE u32 text_gpu_flags(u32 line){return line<vms.size()?vms[line]->flags:0;}
EMSCRIPTEN_KEEPALIVE i32 text_gpu_step(){return constructor_geometry_step();}
EMSCRIPTEN_KEEPALIVE void text_gpu_show(){constructor_interrupt(2);}
EMSCRIPTEN_KEEPALIVE const u8* text_gpu_frame(u32 left,u32 top,u32 width,u32 height){using namespace constructor_text_gpu;if(!width||!height||left+width>640||top+height>480)return nullptr;auto& r=graphics->backend;r.state=touhou::sdl::State{};r.state.target=sdl::GraphicsDevice::screen;r.state.viewport={0,0,640,480,0,1};r.state.layout=attributes(VertexLayout::ScreenColorUv);r.configure_game(1);r.pipeline().depthTest=false;r.pipeline().fog=false;r.pipeline().textureTransform=false;r.pipeline().color.second=r.pipeline().alpha.second={ArgumentSource::Diffuse};r.clear(1,0xff42678b,1,0);
 for(u32 i=0;i<geometry_count();++i){const auto* m=portrait_graphics.materials.data()+i*9;r.state.texture=graphics->texture(resource,m[0]-1);auto& p=r.pipeline();p.depthWrite=m[1];p.sourceBlend=BlendFactor(m[2]-1);p.destinationBlend=BlendFactor(m[3]-1);p.blendEquation=BlendEquation(m[4]-1);p.minFilter=m[5]==1?Filter::Nearest:Filter::Linear;p.magFilter=m[6]==1?Filter::Nearest:Filter::Linear;p.addressU=m[7]==1?Address::Repeat:m[7]==2?Address::Mirror:Address::Clamp;p.addressV=m[8]==1?Address::Repeat:m[8]==2?Address::Mirror:Address::Clamp;u32 triangles[42];const auto* vertices=portrait_graphics.quads.data()+i*28;u32 at=0;for(u32 vertex:{0,1,2,1,2,3})for(u32 f=0;f<7;++f)triangles[at++]=vertices[vertex*7+f];r.draw_batch(2,triangles,28);}
 r.read(sdl::GraphicsDevice::screen);auto* target=graphics->pixels(sdl::GraphicsDevice::screen);for(u32 y=0;y<height;++y)std::memcpy(cropped+y*width*4,target->pixels.data()+((top+y)*640+left)*4,width*4);return cropped;}
EMSCRIPTEN_KEEPALIVE u32 text_gpu_quads(){return geometry_count();}
}

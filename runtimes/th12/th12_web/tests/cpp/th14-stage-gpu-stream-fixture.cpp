#include "../../../portable/sdl/Renderer.hpp"
#include <emscripten.h>
#include <cstring>
#include <cstdlib>
#include <memory>
#include <map>
using namespace touhou::sdl;
namespace {
std::unique_ptr<Renderer> renderer;
std::map<u32,Surface> textures;
u8 pixels[640*480*4]{};
Surface resolve_stream(void*,u32 id){
 if(id==1)return {1,640,480,PixelFormat::Bgra8,640*4,pixels,sizeof(pixels),0};
 if(id==10000)return {10000,640,480,PixelFormat::Depth16,0,nullptr,0,0};
 auto it=textures.find(id);return it==textures.end()?Surface{}:it->second;
}
float value(u32 bits){float f;std::memcpy(&f,&bits,4);return f;}
bool argument(u32 bits,Argument& out){
 switch(bits&15){case 0:out.source=ArgumentSource::Diffuse;break;case 2:out.source=ArgumentSource::Texture;break;case 3:out.source=ArgumentSource::Factor;break;case 4:out.source=ArgumentSource::Specular;break;default:return false;}
 out.complement=bits&16;out.alphaOnly=bits&32;return true;
}
}
extern "C" {
EMSCRIPTEN_KEEPALIVE void* gpu_allocate(u32 n){return std::malloc(n);}
EMSCRIPTEN_KEEPALIVE void gpu_release(void* p){std::free(p);}
// Production GraphicsDevice uses backend version10 even for PORT_TITLE14;
// this enables its alpha conversion, clip control and D16 precision paths.
EMSCRIPTEN_KEEPALIVE int gpu_initialize(){renderer=std::make_unique<Renderer>(10,resolve_stream,nullptr);return renderer->initialize();}
EMSCRIPTEN_KEEPALIVE const char* gpu_error(){return renderer?renderer->error():"uninitialized";}
EMSCRIPTEN_KEEPALIVE int gpu_texture(u32 id,u32 w,u32 h,u32 format,u32 pitch,u8* data,u32 size){
 PixelFormat f;
 switch(format){case 20:f=PixelFormat::Bgr8;break;case 21:f=PixelFormat::Bgra8;break;case 22:f=PixelFormat::Bgrx8;break;case 23:f=PixelFormat::Rgb565;break;case 25:f=PixelFormat::Argb1555;break;case 26:f=PixelFormat::Argb4444;break;case 28:f=PixelFormat::Alpha8;break;default:return 0;}
 if(id<2||id>=10000)return 0;textures[id]={id,w,h,f,pitch,data,size,0};return 1;
}
EMSCRIPTEN_KEEPALIVE int gpu_begin(){
 if(!renderer)return 0;auto& r=*renderer;r.flush();r.state=State{};r.state.target=1;r.state.depth=10000;r.configure_game(1);r.clear(3,0xff42678b,1,0);return 1;
}
EMSCRIPTEN_KEEPALIVE int gpu_render_state(u32 key,u32 v){
 if(!renderer)return 0;auto& p=renderer->pipeline();
 switch(key){
 case 7:p.depthTest=v!=0;break;case 14:p.depthWrite=v!=0;break;case 15:p.alphaTest=v!=0;break;
 case 19:if(v<1||v>11)return 0;p.sourceBlend=BlendFactor(v-1);break;
 case 20:if(v<1||v>11)return 0;p.destinationBlend=BlendFactor(v-1);break;
 case 22:if(v<1||v>3)return 0;p.cull=v==1?Cull::None:v==2?Cull::Back:Cull::Front;break;
 case 23:if(v<1||v>8)return 0;p.depthCompare=Compare(v-1);break;
 case 24:p.alphaReference=v;break;case 25:if(v<1||v>8)return 0;p.alphaCompare=Compare(v-1);break;
 case 27:p.blend=v!=0;break;case 28:p.fog=v!=0;break;case 34:p.fogColor=v;break;
 case 36:p.fogNear=value(v);break;case 37:p.fogFar=value(v);break;case 38:p.fogDensity=value(v);break;
 case 48:p.rangeFog=v!=0;break;case 60:p.textureFactor=v;break;case 168:p.colorMask=v;break;
 case 140:if(v>3)return 0;p.fogMode=FogMode(v);break;
 case 171:if(v<1||v>5)return 0;p.blendEquation=BlendEquation(v-1);break;
 case 35:case 137:case 161:case 194:case 206:if(v)return 0;break;
 default:return 0;
 }return 1;
}
EMSCRIPTEN_KEEPALIVE int gpu_sampler(u32 sampler,u32 key,u32 v){
 if(!renderer||sampler)return 0;auto& p=renderer->pipeline();
 if(key==1||key==2){if(v<1||v>3)return 0;(key==1?p.addressU:p.addressV)=Address(v-1);}
 else if(key==5||key==6){if(v<1||v>2)return 0;(key==5?p.magFilter:p.minFilter)=Filter(v-1);}
 else if((key==7||key==11)&&v==0){}else return 0;return 1;
}
EMSCRIPTEN_KEEPALIVE int gpu_texture_stage(u32 stage,u32 key,u32 v){
 if(!renderer)return 0;if(stage==1&&key==1&&v==1)return 1;if(stage)return 0;auto& p=renderer->pipeline();
 switch(key){
 case 1:case 4:if(v<1||v>16)return 0;(key==1?p.color:p.alpha).operation=ColorOperation(v-1);break;
 case 2:if(!argument(v,p.color.first))return 0;break;case 3:if(!argument(v,p.color.second))return 0;break;
 case 5:if(!argument(v,p.alpha.first))return 0;break;case 6:if(!argument(v,p.alpha.second))return 0;break;
 case 11:if(v)return 0;break;case 24:if(v!=0&&v!=2)return 0;p.textureTransform=v!=0;break;default:return 0;
 }return 1;
}
EMSCRIPTEN_KEEPALIVE int gpu_bind(u32 sampler,u32 handle){if(!renderer||sampler||(handle&&!textures.count(handle)))return 0;renderer->state.texture=handle;return 1;}
EMSCRIPTEN_KEEPALIVE int gpu_fvf(u32 v){
 if(!renderer)return 0;auto& a=renderer->state.layout;
 switch(v){case 0x102:a=attributes(VertexLayout::WorldUv);break;case 0x142:a=attributes(VertexLayout::WorldColorUv);break;case 0x44:a=attributes(VertexLayout::ScreenColor);break;default:return 0;}return 1;
}
EMSCRIPTEN_KEEPALIVE int gpu_matrix(u32 key,const u32* words){
 if(!renderer)return 0;MatrixKind k;
 switch(key){case 256:k=MatrixKind::World;break;case 2:k=MatrixKind::View;break;case 3:k=MatrixKind::Projection;break;case 16:k=MatrixKind::Texture;break;default:return 0;}
 renderer->transform(k,words);return 1;
}
EMSCRIPTEN_KEEPALIVE int gpu_viewport(const u32* w){if(!renderer)return 0;renderer->viewport({w[0],w[1],w[2],w[3],value(w[4]),value(w[5])});return 1;}
EMSCRIPTEN_KEEPALIVE int gpu_clear(u32 flags,u32 color,u32 depth,u32 stencil,const i32* rects,u32 count){if(!renderer)return 0;renderer->clear(flags,color,value(depth),stencil,rects,count);return 1;}
EMSCRIPTEN_KEEPALIVE int gpu_draw(u32 topology,u32 count,u32 stride,const void* words){if(!renderer||topology!=5||(stride!=20&&stride!=24))return 0;renderer->draw(Topology::Strip,count,words,stride);return 1;}
EMSCRIPTEN_KEEPALIVE const u8* gpu_read(){if(!renderer)return nullptr;renderer->read(1);return pixels;}
}

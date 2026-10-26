// Diagnostic access only: replay an observed issue() without rebuilding its
// batches. Renderer.cpp, object layout and all shader arithmetic stay intact.
#include <SDL3/SDL.h>
#include <GLES3/gl3.h>
#include <array>
#include <map>
#include <memory>
#include <string>
#include <vector>
#include <cstring>
#include <cstdlib>
#include "GraphicsState.hpp"
#define private public
#include "../../../portable/sdl/Renderer.hpp"
#undef private
#include <emscripten.h>
using namespace touhou::sdl;
namespace {
std::unique_ptr<Renderer> renderer;
std::map<u32,Surface> resources;
std::vector<u8> pixels;
std::vector<float> probePixels;
std::vector<u8> probeSeed;
Surface resolve_trace(void*,u32 id){auto it=resources.find(id);return it==resources.end()?Surface{}:it->second;}
float value(u32 word){float f;std::memcpy(&f,&word,4);return f;}
State state(const u32* w){
 State s;s.target=w[1];s.depth=w[2];s.texture=w[3];
 s.viewport={w[4],w[5],w[6],w[7],value(w[8]),value(w[9])};s.stride=w[10];
 s.layout={bool(w[11]),w[12],w[13],w[14]};auto& p=s.pipeline;
 p.depthTest=w[15];p.depthWrite=w[16];p.blend=w[17];p.alphaTest=w[18];p.fog=w[19];p.rangeFog=w[20];p.dither=w[21];
 p.depthCompare=Compare(w[22]);p.alphaCompare=Compare(w[23]);p.sourceBlend=BlendFactor(w[24]);p.destinationBlend=BlendFactor(w[25]);
 p.blendEquation=BlendEquation(w[26]);p.cull=Cull(w[27]);p.colorMask=w[28];p.alphaReference=w[29];p.fogColor=w[30];p.textureFactor=w[31];
 p.fogMode=FogMode(w[32]);p.fogNear=value(w[33]);p.fogFar=value(w[34]);p.fogDensity=value(w[35]);
 p.color.operation=ColorOperation(w[36]);p.color.first={ArgumentSource(w[37]),bool(w[38]),bool(w[39])};p.color.second={ArgumentSource(w[40]),bool(w[41]),bool(w[42])};
 p.alpha.operation=ColorOperation(w[43]);p.alpha.first={ArgumentSource(w[44]),bool(w[45]),bool(w[46])};p.alpha.second={ArgumentSource(w[47]),bool(w[48]),bool(w[49])};
 p.textureTransform=w[50];p.minFilter=Filter(w[51]);p.magFilter=Filter(w[52]);p.addressU=Address(w[53]);p.addressV=Address(w[54]);
 std::memcpy(s.matrix.data(),w+55,256);return s;
}
}
extern "C" {
EMSCRIPTEN_KEEPALIVE void* gpu_allocate(u32 n){return std::malloc(n);}
EMSCRIPTEN_KEEPALIVE void gpu_release(void* p){std::free(p);}
EMSCRIPTEN_KEEPALIVE int gpu_initialize(){renderer=std::make_unique<Renderer>(10,resolve_trace,nullptr);return renderer->initialize();}
EMSCRIPTEN_KEEPALIVE const char* gpu_error(){return renderer?renderer->error():"uninitialized";}
EMSCRIPTEN_KEEPALIVE int gpu_surface(u32 id,u32 w,u32 h,u32 format,u32 pitch,u8* data,u32 size,u32 version){
 resources[id]={id,w,h,PixelFormat(format),pitch,data,size,version};return 1;
}
EMSCRIPTEN_KEEPALIVE int gpu_seed(u32 id){renderer->prepare(id);return 1;}
EMSCRIPTEN_KEEPALIVE int gpu_issue(const u32* w,const void* vertices,const void* indices,const void* instances){
 if(w[0]!=0x54524331)return 0;const auto s=state(w);
 renderer->issue(s,Topology(w[119]),w[120],vertices,w[121],indices,IndexType(w[122]),instances,w[124]);return 1;
}
EMSCRIPTEN_KEEPALIVE const float* gpu_probe(const u32* w,const void* vertices){
 if(w[0]!=0x54524331||w[123]||w[124])return nullptr;
 constexpr u32 id=0x70000000;auto& r=*renderer;auto s=state(w);
 probeSeed.resize(640*480*4);resources[id]={id,640,480,PixelFormat::Bgra8,640*4,probeSeed.data(),u32(probeSeed.size()),0};
 auto& g=r.surface(id);r.bind_texture(g.texture);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA32F,640,480,0,GL_RGBA,GL_FLOAT,nullptr);
 r.state.target=id;r.state.depth=0;r.viewport(s.viewport);r.clear(1,0,1,0);
 s.target=id;s.depth=0;s.pipeline.depthTest=false;s.pipeline.depthWrite=false;s.pipeline.blend=false;
 r.issue(s,Topology(w[119]),w[120],vertices,w[121],nullptr,IndexType(w[122]),nullptr,0);
 r.bind_framebuffer(GL_FRAMEBUFFER,g.framebuffer);glPixelStorei(GL_PACK_ALIGNMENT,1);probePixels.resize(640*480*4);
 glReadPixels(0,0,640,480,GL_RGBA,GL_FLOAT,probePixels.data());return probePixels.data();
}
EMSCRIPTEN_KEEPALIVE int gpu_clear(const u32* w,const u32* viewport,const i32* rects,u32 count){
 renderer->state.target=w[0];renderer->state.depth=w[1];renderer->viewport({viewport[0],viewport[1],viewport[2],viewport[3],0,1});
 renderer->clear(w[2],w[3],value(w[4]),w[5],rects,count);return 1;
}
EMSCRIPTEN_KEEPALIVE const u8* gpu_read(u32 id){
 auto& r=*renderer;auto it=r.surfaces.find(id);if(it==r.surfaces.end())return nullptr;
 const auto s=resources.at(id);pixels.resize(s.width*s.height*4);
 r.bind_framebuffer(GL_FRAMEBUFFER,it->second.framebuffer);glPixelStorei(GL_PACK_ALIGNMENT,1);
 glReadPixels(0,0,s.width,s.height,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());
 for(u32 i=0;i<s.width*s.height;i++)std::swap(pixels[i*4],pixels[i*4+2]);return pixels.data();
}
}

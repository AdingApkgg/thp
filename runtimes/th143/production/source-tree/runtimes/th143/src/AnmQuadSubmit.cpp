#include "AnmQuadSubmit.hpp"
#include <cmath>
namespace th143 {
namespace {
u32 multiply_color(u32 color,u32 factor){u32 result=0;for(u32 i=0;i<4;++i){const u32 v=((color>>(i*8)&255)*(factor>>(i*8)&255))>>7;result|=(v<256?v:255)<<(i*8);}return result;}
float aligned(float value,u32 rounding){double result=value;
    if(rounding==1)result=std::floor(result);else if(rounding==2)result=std::ceil(result);else if(rounding==3)result=std::trunc(result);
    else if(std::isfinite(value)&&std::fabs(value)<8388608.f){const double low=std::floor(result),part=result-low;result=part<.5?low:part>.5?low+1:(std::fmod(low,2.0)==0?low:low+1);}
    return float(result-.5);
}
}
bool submit_anm_quad(u32 p,u32 current,AnmView vm,AnmView camera,AnmQuad& quad,u32 flags,AnmRenderMemory& memory,AnmSpriteDevice& device,u32 rounding){
    if(!vm.data||!camera.data)return false;
    auto read=[&](u32 token,u32& value){return memory.read_render_memory(token,&value,4);};auto write=[&](u32 token,u32 value){return memory.write_render_memory(token,&value,4);};
    u32 ox,oy;if(!read(p+0xd0,ox)||!read(p+0xd4,oy))return false;
    std::array<AnmView,4> v={AnmView{quad.vertices[0].data()},AnmView{quad.vertices[1].data()},AnmView{quad.vertices[2].data()},AnmView{quad.vertices[3].data()}};
    for(auto q:v){q.put(0,word(q.floating(0)+real(ox)));q.put(4,word(q.floating(4)+real(oy)));}
    if(flags&1){const u32 x0=word(aligned(v[0].floating(0),rounding)),x1=word(aligned(v[1].floating(0),rounding)),y0=word(aligned(v[0].floating(4),rounding)),y1=word(aligned(v[2].floating(4),rounding));v[0].put(0,x0);v[2].put(0,x0);v[1].put(0,x1);v[3].put(0,x1);v[0].put(4,y0);v[1].put(4,y0);v[2].put(4,y1);v[3].put(4,y1);}
    for(u32 i=0;i<4;++i)for(u32 j=0;j<3;++j)vm.put(0x4f8+i*12+j*4,v[i].get(j*4));
    v[0].put(20,word(vm.floating(0x88)+vm.floating(0x3b8)));v[0].put(24,word(vm.floating(0x3bc)+vm.floating(0x8c)));
    float u=vm.floating(0x3c0)-vm.floating(0x3b8);u*=vm.floating(0x78);u+=vm.floating(0x88)+vm.floating(0x3b8);v[1].put(20,word(u));v[1].put(24,word(vm.floating(0x8c)+vm.floating(0x3c4)));
    v[2].put(20,word(vm.floating(0x88)+vm.floating(0x3c8)));float t=vm.floating(0x3cc)-vm.floating(0x3bc);t*=vm.floating(0x7c);t+=vm.floating(0x8c)+vm.floating(0x3bc);v[2].put(24,word(t));
    u=vm.floating(0x3d0)-vm.floating(0x3c8);u*=vm.floating(0x78);u+=vm.floating(0x88)+vm.floating(0x3c8);v[3].put(20,word(u));t=vm.floating(0x3d4)-vm.floating(0x3c4);t*=vm.floating(0x7c);t+=vm.floating(0x8c)+vm.floating(0x3c4);v[3].put(24,word(t));
    float maxx=v[0].floating(0)>v[1].floating(0)?v[0].floating(0):v[1].floating(0),maxy=v[0].floating(4)>v[1].floating(4)?v[0].floating(4):v[1].floating(4);
    float minx=v[1].floating(0)>v[0].floating(0)?v[0].floating(0):v[1].floating(0),miny=v[1].floating(4)>v[0].floating(4)?v[0].floating(4):v[1].floating(4);
    for(u32 i=2;i<4;++i){if(v[i].floating(0)>maxx)maxx=v[i].floating(0);if(v[i].floating(4)>maxy)maxy=v[i].floating(4);if(minx>v[i].floating(0))minx=v[i].floating(0);if(miny>v[i].floating(4))miny=v[i].floating(4);}
    if(float(camera.get(0xe0))>maxx||float(camera.get(0xe4))>maxy||minx>float(camera.get(0xe8)+camera.get(0xe0))||miny>float(camera.get(0xec)+camera.get(0xe4)))return true;
    u32 texture,cached;if(!read(vm.get(0x2c)+8,texture)||!read(p+0xbc8198,cached))return false;
    if(cached!=texture){u32 native_texture;if(!write(p+0xbc8198,texture)||!flush_anm_quads(p,current,memory,device)||!read(texture,native_texture)||!device.texture(0,native_texture))return false;}
    u8 kind;if(!memory.read_render_memory(p+0xbc819e,&kind,1))return false;if(kind!=1){kind=1;if(!flush_anm_quads(p,current,memory,device)||!memory.write_render_memory(p+0xbc819e,&kind,1))return false;}
    if(!(flags&2)){const u32 mode=(vm.get(0x18)>>17)&3;u32 primary=vm.get(0x534),secondary=vm.get(0x538),tint,enabled;if(!read(p+0xff75a8,enabled)||!read(p+0xff75a4,tint))return false;
        if(mode<2){u32 color=mode?secondary:primary;if((vm.get(0x1c)&0x01000000)&&vm.get(0x594)){u32 parent;if(!read(vm.get(0x594)+0x53c,parent))return false;color=multiply_color(color,parent);}vm.put(0x53c,color);if(enabled)color=multiply_color(color,tint);for(auto q:v)q.put(16,color);}
        else{if(enabled){primary=multiply_color(primary,tint);secondary=multiply_color(secondary,tint);}v[0].put(16,primary);v[1].put(16,mode==2?secondary:primary);v[2].put(16,mode==2?primary:secondary);v[3].put(16,secondary);}
    }
    if(!configure_anm_render(p,current,vm,memory,device))return false;u32 ignored;return append_anm_quad(p,quad,memory,ignored);
}
}

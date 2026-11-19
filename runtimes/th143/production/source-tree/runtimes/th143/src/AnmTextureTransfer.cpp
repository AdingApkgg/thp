#include "AnmTextureTransfer.hpp"
#include <cmath>
namespace th143 {
namespace {
u32 truncated(float value){if(!std::isfinite(value)||double(value)>=2147483648.||double(value)<-2147483648.)return 0x80000000;return u32(i32(value));}
}
bool transfer_anm_texture(const AnmTextureRequest& request,float scale,u32 backbuffer,AnmTextureTransferHost& host,i32& result){
    static constexpr u32 formats[8]={0,21,25,23,20,26,29,28},bpp[8]={4,4,2,2,3,2,2,1};
    if(request.kind==AnmTextureRequest::external||request.format>=8)return false;
    auto read=[&](u32 p,u32& value){return host.read_texture_memory(p,&value,4);};auto write=[&](u32 p,u32 value){return host.write_texture_memory(p,&value,4);};
    u32 flags;if(!read(request.entry+0x14,flags))return false;
    if(request.kind==AnmTextureRequest::render_target){
        if(!write(request.entry+0x14,flags|1))return false;AnmDeviceTextureRequest create{true,request.width,request.height,1,1,21,0};i32 hr;if(!host.create_device_texture(create,request.entry,hr)||!write(request.entry+0xc,backbuffer==21?4:2))return false;result=0;return true;
    }
    if(!write(request.entry+0x14,flags&~1u))return false;
    AnmDeviceTextureRequest create{false,request.width,request.height,1,0,formats[request.format],1};
    if(request.kind==AnmTextureRequest::blank){i32 hr;if(!host.create_device_texture(create,request.entry,hr)||!write(request.entry+0xc,bpp[request.format]))return false;result=i32(bpp[request.format]*request.width*request.height);return true;}
    u32 header;if(!read(request.entry+0x10,header))return false;u8 resized;std::int16_t sw,sh,sf;if(!host.read_texture_memory(header+0x22,&resized,1)||!host.read_texture_memory(request.source+8,&sw,2)||!host.read_texture_memory(request.source+10,&sh,2)||!host.read_texture_memory(request.source+6,&sf,2)||sf<0||sf>=8)return false;
    AnmSurfaceUpload upload;upload.source=request.source+16;upload.format=formats[sf];upload.pitch=u32(i32(sw))*bpp[sf];upload.source_rect={0,0,i32(sw),i32(sh)};upload.destination=upload.source_rect;
    if(resized&&scale<2.f){float v=float(sw)*scale;upload.destination[2]=i32(truncated(v*.5f));v=float(sh)*scale;upload.destination[3]=i32(truncated(v*.5f));v=float(i32(request.width))*scale;create.width=truncated(v*.5f);v=float(i32(request.height))*scale;create.height=truncated(v*.5f);upload.filter=0x30004;}
    i32 hr;if(!host.create_device_texture(create,request.entry,hr))return false;if(hr!=0){result=-1;return true;}
    u32 texture,surface=0;if(!read(request.entry,texture)||!host.texture_surface(texture,0,surface,hr))return false;upload.surface=surface;
    if(!host.upload_texture_surface(upload,hr)||!write(request.entry+0xc,bpp[request.format]))return false;if(surface&&!host.release_texture_object(surface))return false;
    result=i32(bpp[request.format]*create.width*create.height);return true;
}
}

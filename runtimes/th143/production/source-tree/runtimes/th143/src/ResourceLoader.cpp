#include "ResourceLoader.hpp"

namespace th143 {
namespace {
struct Memory {
    ResourceLoaderHost& h;
    template<class T>bool read(u32 p,T& v){return h.read(p,&v,sizeof(v));}
    bool get(u32 p,u32& v){return read(p,v);}
    template<class T>bool write(u32 p,const T& v){return h.write(p,&v,sizeof(v));}
    bool zero(u32 p,u32 n){std::array<u8,256> b{};while(n){u32 part=n>256?256:n;if(!h.write(p,b.data(),part))return false;p+=part;n-=part;}return true;}
    bool string(u32 p,std::string& s){s.clear();for(u32 i=0;i<1024;++i){u8 c;if(!read(p+i,c))return false;if(!c)return true;s.push_back(char(c));}return false;}
};
bool chunk(u32 resource,u32 index,u32 first_sprite,u32 first_script,u32 source,ResourceLoaderHost& h,i32& status){
    Memory m{h};u32 version,texture_table,sprite_table,scripts,file;
    if(!m.get(source,version))return false;if(version!=8){status=-1;return true;}
    if(!m.get(resource+0x124,texture_table)||!m.get(resource+0x11c,sprite_table)||!m.get(resource+0x120,scripts)||!m.get(resource,file))return false;
    const u32 entry=texture_table+index*24;if(!m.write(entry+16,source))return false;
    u8 embedded;u16 width,height,format,sprite_count,script_count;
    if(!m.read(source+0x20,embedded)||!m.read(source+0xa,width)||!m.read(source+0xc,height)||!m.read(source+0xe,format)||!m.read(source+4,sprite_count)||!m.read(source+6,script_count))return false;
    AnmTextureRequest request;request.entry=entry;request.width=width;request.height=height;request.format=format;
    if(embedded){u32 offset;if(!m.get(source+0x1c,offset))return false;request.kind=AnmTextureRequest::embedded;request.source=source+offset;}
    else{
        u32 offset;u8 name[2];if(!m.get(source+0x10,offset)||!h.read(source+offset,name,2))return false;
        if(name[0]=='@'){
            request.kind=name[1]=='R'?AnmTextureRequest::render_target:AnmTextureRequest::blank;
            if(request.kind==AnmTextureRequest::render_target){request.width=h.resource_viewport_width();request.height=h.resource_viewport_height();width=u16(request.width);height=u16(request.height);if(!m.write(source+0xa,width)||!m.write(source+0xc,height))return false;}
        }else{
            request.kind=AnmTextureRequest::external;std::int16_t x,y;if(!m.read(source+0x14,x)||!m.read(source+0x16,y)||!m.get(entry+4,request.source)||!m.get(entry+8,request.source_bytes))return false;request.x=x;request.y=y;
        }
    }
    u32 physical_width,physical_height;
    if(!h.create_resource_texture(request,status,physical_width,physical_height))return false;
    if(request.kind!=AnmTextureRequest::render_target){u32 total;if(!m.get(resource+0x130,total)||!m.write(resource+0x130,total+u32(status)))return false;}
    if(status<0&&(request.kind==AnmTextureRequest::embedded||request.kind==AnmTextureRequest::external))return true;
    const float w=float(physical_width),height_pixels=float(physical_height),sx=w/float(width),sy=height_pixels/float(height);
    u32 cursor=source+0x40;
    for(u32 i=0;i<sprite_count;++i){u32 offset;if(!m.get(cursor,offset))return false;float x,y,dx,dy;
        if(!m.read(source+offset+4,x)||!m.read(source+offset+8,y)||!m.read(source+offset+12,dx)||!m.read(source+offset+16,dy))return false;
        const float left=x*sx,top=y*sy,right=(x+dx)*sx,bottom=(y+dy)*sy;
        const std::array<u32,17> d{file,index,entry,word(left),word(top),word(right),word(bottom),word(height_pixels),word(w),word(left/w),word(top/height_pixels),word(right/w),word(bottom/height_pixels),word((bottom-top)/sy),word((right-left)/sx),word(sx),word(sy)};
        if(!h.write(sprite_table+(first_sprite+i)*72,d.data(),68))return false;cursor+=4;
    }
    cursor+=4;for(u32 i=0;i<script_count;++i){u32 offset;if(!m.get(cursor,offset)||!m.write(scripts+(first_script+i)*4,source+offset))return false;cursor+=8;}
    status=1;return true;
}
}
bool request_anm_resource(u32 manager,u32 index,const std::string& name,ResourceLoaderHost& h,u32& resource){
    Memory m{h};resource=0;if(index>=30||name.size()>255)return false;
    const u32 slot=manager+0xbc7b0c+index*4;if(!m.get(slot,resource))return false;if(resource)return true;
    if(!h.allocate_resource_storage(0x13c,false,resource)||!m.zero(resource,0x13c)||!m.write(slot,resource)||!m.write(resource,index))return false;
    u32 raw,size;if(!h.read_resource_file(name,false,raw,size))return false;
    if(!raw){if(!h.release_resource_storage(resource))return false;resource=0;return true;}
    if(!m.write(resource+0x108,raw)||!h.write(resource+4,name.c_str(),u32(name.size()+1)))return false;
    u32 source=raw,chunks=0,sprites=0,scripts=0;
    for(u32 budget=0;budget<4096;++budget){u16 a,b;u32 next;if(!m.read(source+4,a)||!m.read(source+6,b)||!m.get(source+0x24,next))return false;
        ++chunks;sprites+=a;scripts+=b;if(!next)break;source+=next;if(budget==4095)return false;
    }
    u32 textures,sprite_table,script_table,templates;
    if(chunks>4096||sprites>1000000||scripts>100000)return false;
    if(!m.write(resource+0x110,chunks)||!h.allocate_resource_storage(chunks*24,true,textures)||!m.write(resource+0x124,textures)||!m.zero(textures,chunks*24)||!h.allocate_resource_storage(sprites*72,true,sprite_table)||!m.write(resource+0x11c,sprite_table)||!h.allocate_resource_storage(scripts*4,true,script_table)||!m.write(resource+0x120,script_table)||!m.write(resource+0x114,scripts)||!m.write(resource+0x118,sprites))return false;
    source=raw;bool prepared=true;
    for(u32 i=0;i<chunks;++i){u32 version,next;u8 embedded;if(!m.get(source,version)||!m.read(source+0x20,embedded)||!m.get(source+0x24,next))return false;
        if(version!=8){prepared=false;break;}
        if(!embedded){u32 offset;u8 first;if(!m.get(source+0x10,offset)||!m.read(source+offset,first))return false;
            if(first!='@'){std::string external;u32 bytes=0,token=0;if(!m.string(source+offset,external)||!h.read_resource_file(external,true,token,bytes))return false;if(!token){prepared=false;break;}if(!m.write(textures+i*24+8,bytes)||!m.write(textures+i*24+4,token))return false;}
        }source+=next;
    }
    if(prepared&&(!h.allocate_resource_storage(scripts*AnmView::bytes,true,templates)||!m.write(resource+0x10c,templates)||!m.zero(templates,scripts*AnmView::bytes)))return false;
    return m.write(resource+0x128,u32(1));
}
bool complete_anm_resource_chunk(u32 resource,ResourceLoaderHost& h,u32& result){
    Memory m{h};u32 source,pending;if(!m.get(resource+0x108,source)||!m.get(resource+0x128,pending))return false;
    u32 sprite=0,script=0;
    for(u32 i=0;i<4096;++i){
        if(i==pending-1){i32 status;if(!chunk(resource,i,sprite,script,source,h,status))return false;if(status<0){result=0;return m.write(resource+0x128,u32(0));}}
        u16 a,b;u32 next;if(!m.read(source+4,a)||!m.read(source+6,b)||!m.get(source+0x24,next))return false;sprite+=a;script+=b;
        if(!next){u32 count,templates;if(!m.get(resource+0x114,count)||!m.get(resource+0x10c,templates))return false;
            for(u32 j=0;j<count;++j)if(!h.build_resource_template(templates+j*AnmView::bytes,resource,j))return false;
            result=resource;return m.write(resource+0x128,u32(0));
        }
        source+=next;if(i+1==pending){result=resource;return m.write(resource+0x128,pending+1);}
    }return false;
}
}


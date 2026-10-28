#include "../../cpp/game/AnmTransferTh14.hpp"
#include <emscripten.h>
#include <tuple>
using namespace th11;
namespace {
bool same(const AnmResource& a,const AnmResource& b){
    if(a.textures.size()!=b.textures.size()||a.sprites.size()!=b.sprites.size()||a.scripts.size()!=b.scripts.size()||b.templates||b.last_error||!b.detail.empty())return false;
    for(u32 i=0;i<a.textures.size();++i){const auto& x=a.textures[i];const auto& y=b.textures[i];
        if(std::tie(x.name,x.kind,x.width,x.height,x.format,x.pixel_width,x.pixel_height,x.pixel_format,x.source_x,x.source_y,x.priority,x.half_resolution,x.first_script,x.script_count)!=
           std::tie(y.name,y.kind,y.width,y.height,y.format,y.pixel_width,y.pixel_height,y.pixel_format,y.source_x,y.source_y,y.priority,y.half_resolution,y.first_script,y.script_count)||x.pixels!=y.pixels)return false;
    }
    static_assert(sizeof(AnmSprite)==40);
    if(!a.sprites.empty()&&std::memcmp(a.sprites.data(),b.sprites.data(),a.sprites.size()*sizeof(AnmSprite)))return false;
    for(u32 i=0;i<a.scripts.size();++i){const auto& x=a.scripts[i];const auto& y=b.scripts[i];
        if(std::tie(x.source_id,x.file_offset,x.load_hash)!=std::tie(y.source_id,y.file_offset,y.load_hash)||x.bytes!=y.bytes)return false;
    }
    return true;
}
u32 counts[5]{};
}
extern "C" {
EMSCRIPTEN_KEEPALIVE int fixture_compare(const u8* source,u32 source_size,const u8* packet,u32 size){
    AnmResource direct,delivered;u32 identity_size=0,identity_hash=0;
    if(!direct.open(source,source_size))return -1;
    if(!th14_decode_anm_transfer(packet,size,delivered,&identity_size,&identity_hash))return -2;
    if(identity_size!=source_size||identity_hash!=anm_bytes_hash(source,source_size))return -3;
    if(!same(direct,delivered))return -4;
    counts[0]=u32(direct.textures.size());counts[1]=u32(direct.sprites.size());counts[2]=u32(direct.scripts.size());counts[3]=counts[4]=0;
    for(const auto& t:direct.textures)counts[3]+=u32(t.pixels.size());
    for(const auto& s:direct.scripts)counts[4]+=u32(s.bytes.size());
    return 1;
}
EMSCRIPTEN_KEEPALIVE u32 fixture_count(u32 field){return field<5?counts[field]:0;}
EMSCRIPTEN_KEEPALIVE int fixture_reject(const u8* packet,u32 size){
    AnmResource output;output.last_error=77;output.detail="unchanged";output.sprites.resize(1);output.sprites[0].source_id=12345;
    if(th14_decode_anm_transfer(packet,size,output))return 0;
    return output.last_error==77&&output.detail=="unchanged"&&output.textures.empty()&&output.scripts.empty()&&output.sprites.size()==1&&output.sprites[0].source_id==12345;
}
}

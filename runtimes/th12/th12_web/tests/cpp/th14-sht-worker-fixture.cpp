#include "../../cpp/game/GameResources.hpp"
#include "../../cpp/game/ShotFiles.hpp"
#include "../../cpp/game/ShtTransferTh14.hpp"
#include <cstdlib>
using namespace th11;
namespace {
GameResources source;
ShtResource baseline,imported;
std::string selected;
std::vector<u8> packet,raw_source,canonical;
u32 delivery_mode=0,packet_copies=0,raw_copies=0,resource_queries=0;
}
#define API(name) extern "C" __attribute__((export_name(#name)))
extern "C" {
int th14_webgpu_resource_size(unsigned kind,const char* name){
    ++resource_queries;if(!delivery_mode||selected!=name||kind!=3)return -1;
    return delivery_mode==2?-2:delivery_mode==4?-1:int(packet.size());
}
int th14_webgpu_resource_copy(unsigned kind,const char* name,void* data,unsigned size){
    ++packet_copies;
    if(kind!=3||selected!=name||delivery_mode==3||size!=packet.size())return 0;
    if(size)std::memcpy(data,packet.data(),size);return 1;
}
int th14_webgpu_archive_size(const char* name){return delivery_mode&&selected==name?int(raw_source.size()):-1;}
int th14_webgpu_archive_copy(const char* name,void* data,unsigned size){
    ++raw_copies;if(selected!=name||size!=raw_source.size())return 0;
    if(size)std::memcpy(data,raw_source.data(),size);return 1;
}
int th14_webgpu_anm_size(const char*){return -1;}
int th14_webgpu_anm_copy(const char*,void*,unsigned){return 0;}
}
API(fixture_allocate) void* fixture_allocate(u32 size){return std::malloc(size);}
API(fixture_release) void fixture_release(void* memory){std::free(memory);}
API(fixture_open) u32 fixture_open(const u8* data,u32 size){return source.open_archive(data,size);}
API(fixture_select) u32 fixture_select(u32 index){
    if(index>=6)return 0;delivery_mode=0;selected=shot_file_name(index);
    baseline={};imported={};packet.clear();raw_source.clear();canonical.clear();
    if(!source.open_sht(selected,baseline)||!source.read(selected,raw_source))return 0;
    return th14_encode_sht_transfer(baseline,raw_source.data(),u32(raw_source.size()),canonical);
}
API(fixture_packet) u32 fixture_packet(const u8* data,u32 size){
    if(!data||size>sht_transfer_th14::maximum_bytes+1)return 0;
    packet.assign(data,data+size);return 1;
}
API(fixture_import) u32 fixture_import(u32 mode){
    if(mode<1||mode>4)return 0;packet_copies=raw_copies=resource_queries=0;delivery_mode=mode;
    const bool ok=source.open_sht(selected,imported);delivery_mode=0;return ok;
}
API(fixture_compare) u32 fixture_compare(){
    static_assert(sizeof(ShtHeader)==640&&sizeof(ShotSpec)==88);
    if(std::memcmp(&baseline.header,&imported.header,sizeof(ShtHeader))||baseline.groups.size()!=imported.groups.size())return 0;
    for(u32 i=0;i<baseline.groups.size();++i){const auto& a=baseline.groups[i];const auto& b=imported.groups[i];
        if(a.metadata!=b.metadata||a.shots.size()!=b.shots.size())return 0;
        for(u32 j=0;j<a.shots.size();++j)if(std::memcmp(&a.shots[j],&b.shots[j],sizeof(ShotSpec)))return 0;
    }return 1;
}
API(fixture_canonical_data) const u8* fixture_canonical_data(){return canonical.data();}
API(fixture_canonical_size) u32 fixture_canonical_size(){return u32(canonical.size());}
API(fixture_value) u32 fixture_value(u32 field){
    if(field==0)return baseline.header.group_count;
    if(field==1){u32 count=0;for(const auto& group:baseline.groups)count+=u32(group.shots.size());return count;}
    return field==2?packet_copies:field==3?raw_copies:field==4?resource_queries:0;
}
API(fixture_error) const char* fixture_error(){return source.error().c_str();}

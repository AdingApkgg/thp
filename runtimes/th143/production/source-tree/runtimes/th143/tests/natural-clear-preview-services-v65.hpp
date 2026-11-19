// Experimental completion composition. GPU bytes come only from the live host
// renderer. Uninitialized native stack residue is not yet reproduced exactly.
#include "../src/PreviewReadback.hpp"
#include "../src/SavedPreviewWriter.hpp"
#include <cstdio>
extern "C" __attribute__((import_module("th143"),import_name("title_clear_surface_read"))) th143::u32 title_clear_surface_read(th143::u32,th143::u32,th143::u32,th143::u8*,th143::u32);
struct NaturalClearPreviewReadback:th143::PreviewReadbackHost {
    std::vector<u8> staging;std::vector<u32> events;u32 width=0,height=0;
    bool create_preview_surface(u32 w,u32 h,u32 format,u32 pool,u32& surface,i32& status)override{if(format!=21||pool!=2)return false;width=w;height=h;staging.resize(w*h*4);surface=0x6e036800;status=0;events.insert(events.end(),{0,w,h,format,pool});return true;}
    bool copy_preview_surface(u32 source,u32 destination,i32& status)override{if(destination!=0x6e036800||!title_clear_surface_read(source,width,height,staging.data(),u32(staging.size())))return false;status=0;events.insert(events.end(),{1,source,destination,u32(staging.size())});return true;}
    bool lock_preview_surface(u32 surface,const u8*& pixels,u32& accessible,u32& pitch,i32& status)override{if(surface!=0x6e036800)return false;pixels=staging.data();accessible=u32(staging.size());pitch=width*4;status=0;events.insert(events.end(),{2,pitch,0x82000000});return true;}
    bool unlock_preview_surface(u32 surface)override{if(surface!=0x6e036800)return false;events.push_back(3);return true;}
    bool release_preview_surface(u32 surface)override{if(surface!=0x6e036800)return false;events.push_back(4);return true;}
}natural_clear_readback;
struct NaturalClearPreviewFile:th143::SavedPreviewWriteHost {
    std::uint64_t filetime=116444736000000000ull;std::string name;
    std::vector<std::vector<u8>> writes;std::vector<u32> events;u32 allocations=0;
    bool preview_directory(u32 phase)override{events.insert(events.end(),{0,phase});return true;}
    bool preview_make_directory()override{events.push_back(1);return true;}
    bool preview_filetime(std::uint64_t& value)override{value=filetime;return true;}
    bool preview_open(const std::string& path,u32& handle)override{name=path;writes.clear();handle=0x1234;events.insert(events.end(),{2,handle});return true;}
    bool preview_write(u32 handle,const u8* bytes,u32 count,u32& written)override{if(handle!=0x1234)return false;writes.emplace_back(bytes,bytes+count);written=count;events.insert(events.end(),{3,handle,count});return true;}
    bool preview_close(u32 handle)override{if(handle!=0x1234)return false;events.insert(events.end(),{4,handle});return campaign_preview_files.commit(name,writes);}
    bool preview_allocate_payload(u32 count,u32& token)override{token=0x7d100000+allocations++*0x100000;events.insert(events.end(),{5,count,token});return true;}
    bool preview_release_payload(u32 token)override{events.insert(events.end(),{6,token});return true;}
}natural_clear_file;
static bool title_natural_clear_preview(u32 day,u32 within){
    u8* pixels=nullptr;u32 accessible=0;
    for(auto& storage:title_root_aux->storage)if(storage.token==title_root_aux->independent.pixels){pixels=storage.bytes.data();accessible=u32(storage.bytes.size());break;}
    PreviewReadbackParameters read;read.screen_width=world->width;read.screen_height=world->height;read.width=title_root_aux->width;read.height=title_root_aux->height;read.source_surface=title_root_aux->independent.surface;i32 result;
    if(!readback_clear_preview(pixels,accessible,read,natural_clear_readback,result))return false;
    SavedPreviewWriteParameters parameters;parameters.flags=title_root_aux->independent.signals;parameters.width=title_root_aux->width;parameters.height=title_root_aux->height;parameters.bytes_per_pixel=title_root_aux->bytes_per_pixel;parameters.day=day;parameters.within_day=within;
    // Undefined x86 stack bytes remain an explicit unpassed comparison frontier.
    parameters.stack_bytes.fill(0);char name[40];std::snprintf(name,sizeof name,"sc%02u_%02u.dat",day+1,within+1);
    const u32 n=parameters.width*parameters.height*parameters.bytes_per_pixel;if(n>accessible)return false;campaign_preview_input_pixels.assign(pixels,pixels+n);return write_saved_preview(name,pixels,accessible,parameters,common_save->codec,natural_clear_file);
}
API(title_clear_preview_time) void title_clear_preview_time(u32 low,u32 high){natural_clear_file.filetime=std::uint64_t(low)|(std::uint64_t(high)<<32);}
API(title_clear_preview_readback_words) u32 title_clear_preview_readback_words(){return natural_clear_readback.events.size();}
API(title_clear_preview_readback_data) const u32* title_clear_preview_readback_data(){return natural_clear_readback.events.data();}
API(title_clear_preview_file_writes) u32 title_clear_preview_file_writes(){return natural_clear_file.writes.size();}
API(title_clear_preview_file_bytes) u32 title_clear_preview_file_bytes(u32 i){return i<natural_clear_file.writes.size()?natural_clear_file.writes[i].size():0;}
API(title_clear_preview_file_data) const u8* title_clear_preview_file_data(u32 i){return i<natural_clear_file.writes.size()?natural_clear_file.writes[i].data():nullptr;}
API(title_clear_preview_file_name) const char* title_clear_preview_file_name(){return natural_clear_file.name.c_str();}
API(title_clear_preview_stack_exact) u32 title_clear_preview_stack_exact(){return 0;}

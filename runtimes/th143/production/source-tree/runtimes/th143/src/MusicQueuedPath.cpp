#include "MusicQueuedPath.hpp"
namespace th143 {
bool queue_music_cached_path(AnmView audio,u32 bytes,u32 path,AudioActionMainPumpHost& host,u32& result){
    if(!audio.data||bytes<0x57b0)return false;if(!audio.get(0x5778)){result=0xffffffff;return true;}
    constexpr u32 base=0x53b1e0;if(path<base||path-base>=bytes)return false;const u32 offset=path-base;u32 length=0;while(length<256&&offset+length<bytes&&audio.data[offset+length])++length;if(length==256||offset+length>=bytes)return false;
    u32 slash=0,backslash=0;bool forward=false;for(u32 i=0;i<length;++i){if(audio.data[offset+i]=='/'){forward=true;slash=i+1;}if(audio.data[offset+i]=='\\')backslash=i+1;}
    if(length-(forward?slash:backslash)>127)return false;
    const u8* table=nullptr;u32 available=0,index=0;if(!host.music_track_table(audio.get(0x1980),table,available)||!find_music_track(table,available,reinterpret_cast<const char*>(audio.data+offset),length+1,index))return false;
    AnmView owner{nullptr},stream{nullptr},meta{nullptr};const u32 metadata=audio.get(0x1980)+index*52;
    if(!host.music_region(audio.get(0x5778),0xa0,owner)||!owner.data||!host.music_region(owner.get(12),0xa0,stream)||!stream.data||!host.music_region(metadata,0x34,meta)||!meta.data)return false;
    u32 ignored=0;if(!reopen_music_file(stream,0xa0,meta,metadata,0,host.music_file_base(),host,ignored))return false;
    //Re-read source bytes after reopening: a file/log callback may have changed
    //the cached name. The source/destination path slots are distinct here.
    for(u32 i=0;i<256;++i){if(offset+i>=bytes||0x1984+i>=bytes)return false;const u8 value=audio.data[offset+i];audio.data[0x1984+i]=value;if(!value){result=0;return true;}}
    return false;
}
}

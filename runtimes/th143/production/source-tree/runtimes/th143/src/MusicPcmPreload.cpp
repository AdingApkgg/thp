#include "MusicPcmPreload.hpp"
#include <cstring>
namespace th143 {
bool preload_music_pcm(AnmView audio,u32 audio_bytes,const u8* table,u32 table_bytes,
                       u32 slot,const char* name,u32 name_bytes,u8 flags,
                       MusicPcmPreloadHost& host,u32& result){
    if(!audio.data||audio_bytes<0x57b0||slot>=16||!name)return false;
    u32 length=0;while(length<name_bytes&&name[length])++length;
    if(length==name_bytes||length>=256)return false;
    constexpr u32 cache_base=0x18bc,path_base=0x4678;
    const u32 cache_at=cache_base+slot*4,path_at=path_base+slot*256,old=audio.get(cache_at);
    if(old){u32 n=0;while(n<=length&&audio.data[path_at+n]==u8(name[n])){if(!name[n]){result=0;return true;}++n;}}
    std::memcpy(audio.data+path_at,name,length+1);
    if(!(flags&0x10)||!audio.get(12)){result=0;return true;}
    if(old){if(!host.free_music_cache(old))return false;audio.put(cache_at,0);}
    const char* filename=reinterpret_cast<const char*>(audio.data+0x5678);
    u32 file_length=0;while(file_length<256&&filename[file_length])++file_length;if(file_length==256)return false;
    u32 handle=0xffffffff;if(!host.open_music_file(filename,0x80000000,1,3,0x08000080,handle))return false;
    if(handle==0xffffffff){if(!host.music_load_error(filename))return false;result=0xffffffff;return true;}
    u32 track=0;if(!find_music_track(table,table_bytes,name,name_bytes,track))return false;
    const u32 entry=track*0x34;if(entry>table_bytes||table_bytes-entry<24)return false;
    u32 offset,bytes;std::memcpy(&offset,table+entry+16,4);std::memcpy(&bytes,table+entry+20,4);
    if(!host.seek_music_file(handle,offset))return false;
    u32 token=0;if(!host.allocate_music_cache(bytes,token))return false;
    if(!token){if(!host.close_music_file(handle)||!host.music_load_error(filename)||!host.music_load_progress(2))return false;result=0xffffffff;return true;}
    if(!host.read_music_file(handle,token,bytes)||!host.close_music_file(handle)||!host.music_load_progress(2))return false;
    audio.put(0x187c+slot*4,audio.get(0x1980)+entry);audio.put(cache_at,token);audio.put(0x18fc+slot*4,token);audio.put(0x193c+slot*4,bytes);
    result=0;return true;
}
}

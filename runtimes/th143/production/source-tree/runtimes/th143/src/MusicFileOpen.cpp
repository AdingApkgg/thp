#include "MusicFileOpen.hpp"
namespace th143 {
bool open_music_file(AnmView s,u32 bytes,u32 path,AnmView meta,u32 metadata,u32 file_base,MusicFileOpenHost& host,u32& result){
    if(!s.data||bytes<0xa0)return false;if(!path){result=0x80070057;return true;}
    if(!host.log_music_open(path))return false;u32 handle;if(!host.create_music_file(path,handle))return false;s.put(0x8c,handle);
    if(handle==0xffffffff){u32 error=0,message=path;if(!host.music_last_error(error)||!host.format_music_error(error,message)||!host.log_music_error(message)||!host.free_music_error(message))return false;result=0x80004005;return true;}
    s.put(0x90,metadata);s.put(0x94,path);u32 ignored=0;if(!reset_music_stream(s,meta,0,0,file_base,host,ignored))return false;s.put(0x2c,s.get(8));s.put(0x9c,0);result=0;return true;
}
bool reopen_music_file(AnmView s,u32 bytes,AnmView meta,u32 metadata,u32 position,u32 file_base,MusicFileOpenHost& host,u32& result){
    if(!s.data||bytes<0xa0)return false;if(s.get(0x7c)){result=0x80004005;return true;}
    if(s.get(0x8c)==0xffffffff){s.put(0x78,1);s.put(0x7c,0);u32 ignored=0;if(!open_music_file(s,bytes,s.get(0x94),meta,metadata,file_base,host,ignored))return false;if(s.get(0x8c)==0xffffffff){result=0x80004005;return true;}}
    if(!meta.data)return false;s.put(0x9c,0);s.put(0x90,metadata);if(!host.log_music_metadata(metadata,meta.get(0x18),meta.get(0x1c)))return false;
    u32 ignored=0;if(!reset_music_stream(s,meta,0,position,file_base,host,ignored))return false;s.put(0x2c,s.get(8));result=0;return true;
}
}

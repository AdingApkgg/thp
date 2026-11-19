#include "MusicOwnerConstruct.hpp"
namespace th143 {
static bool ctor_stream(AnmView object,MusicOwnerConstructHost& host,AnmView& s,AnmView& meta){return host.music_fill_region(object.get(12),0xa0,s)&&s.data&&host.music_fill_region(s.get(0x90),0x34,meta)&&meta.data;}
static bool ctor_silence(AnmView object,u32 destination,u32 bytes,MusicOwnerConstructHost& host){AnmView s{nullptr},meta{nullptr};if(!ctor_stream(object,host,s,meta))return false;std::uint16_t bits;std::memcpy(&bits,meta.data+0x2e,2);return host.fill_music_bytes(destination,bits==8?128:0,bytes);}
static bool ctor_fill(AnmView object,u32 buffer,u32 stream_token,MusicOwnerConstructHost& host){
    u32 status=stream_token,hr=0;if(!host.music_buffer_status(buffer,status,hr))return false;if(signed_word(hr)<0)return true;if((status&2)&&!restore_lost_music_buffer(buffer,host))return false;
    MusicBufferLock lock;if(!host.lock_music_data(buffer,object.get(8),lock,hr))return false;if(signed_word(hr)<0)return true;
    AnmView s{nullptr},meta{nullptr};if(!ctor_stream(object,host,s,meta)||!reset_music_stream(s,meta,0,0,host.music_fill_file_base(),host,hr))return false;
    if(!host.music_fill_region(object.get(12),0xa0,s)||!s.data)return false;u32 count=0;if(!read_music_stream(s,lock.first,lock.bytes,true,count,host,hr))return false;if(signed_word(hr)<0)return true;
    if(!count){if(!ctor_silence(object,lock.first,lock.bytes,host))return false;}else if(count<lock.bytes&&!ctor_silence(object,lock.first+count,lock.bytes-count,host))return false;
    return host.unlock_music_data(buffer,lock,hr);
}
bool construct_music_owner(AnmView object,u32 bytes,u32 token,u32 buffer,u32 buffer_bytes,u32 stream,MusicOwnerConstructHost& host,u32& result){
    if(!object.data||bytes<0xa0)return false;object.put(0,0x4c9b3c);u32 array_token=0;if(!host.allocate_music_owner_array(4,array_token))return false;object.put(4,array_token);
    AnmView array{nullptr};if(!host.music_fill_region(array_token,4,array)||!array.data)return false;array.put(0,buffer);object.put(8,buffer_bytes);object.put(12,stream);object.put(0x10,1);
    if(buffer&&!ctor_fill(object,buffer,stream,host))return false;
    // The original dereferences a null first buffer at this final call.
    if(!host.music_fill_region(object.get(4),4,array)||!array.data||!array.get(0))return false;u32 ignored=0;if(!host.position_music_buffer(array.get(0),0,ignored))return false;
    object.put(0x50,0);object.put(0x54,0);result=token;return true;
}
bool construct_memory_music_owner(AnmView object,u32 bytes,u32 token,u32 buffer,u32 buffer_bytes,u32 stream,u32 segment,MusicOwnerConstructHost& host,u32& result){
    if(!construct_music_owner(object,bytes,token,buffer,buffer_bytes,stream,host,result))return false;object.put(0x94,segment);object.put(0,0x4c9b34);object.put(0x80,0);object.put(0x84,0);object.put(0x88,0);object.put(0x90,0);return true;
}
}

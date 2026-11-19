#include "MusicBufferFill.hpp"
namespace th143 {
static bool stream_view(AnmView object,MusicBufferFillHost& host,AnmView& s){return host.music_fill_region(object.get(12),0xa0,s)&&s.data;}
static bool reset_fill_stream(AnmView object,u32 loop,u32 position,MusicBufferFillHost& host,u32& result){
    AnmView s{nullptr},meta{nullptr};if(!stream_view(object,host,s)||!host.music_fill_region(s.get(0x90),0x34,meta)||!meta.data)return false;return reset_music_stream(s,meta,loop,position,host.music_fill_file_base(),host,result);
}
static bool read_fill_stream(AnmView object,u32 destination,u32 bytes,u32& actual,MusicBufferFillHost& host,u32& result){AnmView s{nullptr};return stream_view(object,host,s)&&read_music_stream(s,destination,bytes,true,actual,host,result);}
static bool silence_fill(AnmView object,u32 destination,u32 bytes,MusicBufferFillHost& host){
    AnmView s{nullptr},meta{nullptr};if(!stream_view(object,host,s)||!host.music_fill_region(s.get(0x90),0x34,meta)||!meta.data)return false;std::uint16_t bits;std::memcpy(&bits,meta.data+0x2e,2);return host.fill_music_bytes(destination,bits==8?128:0,bytes);
}
bool fill_music_buffer(AnmView object,u32 object_bytes,u32 buffer,u32 loop,u32 position,MusicBufferFillOperation operation,u32 explicit_bytes,MusicBufferFillHost& host,u32& result){
    if(!object.data||object_bytes<0xa0)return false;if(!buffer){result=0x800401f0;return true;}
    u32 status=buffer;if(!host.music_buffer_status(buffer,status,result))return false;if(signed_word(result)<0)return true;if((status&2)&&!restore_lost_music_buffer(buffer,host))return false;
    MusicBufferLock lock;const u32 requested=operation==MusicBufferFillOperation::Full?object.get(8):explicit_bytes;if(!host.lock_music_data(buffer,requested,lock,result))return false;if(signed_word(result)<0)return true;
    // The initial reset HRESULT is deliberately ignored before the first read.
    if(!reset_fill_stream(object,0,position,host,result))return false;u32 count=0;if(!read_fill_stream(object,lock.first,lock.bytes,count,host,result))return false;if(signed_word(result)<0)return true;
    u32 total=count;
    if(!total){if(!silence_fill(object,lock.first,lock.bytes,host))return false;}
    else if(total<lock.bytes){
        if(loop){for(u32 steps=0;total<lock.bytes;++steps){if(steps==1000000)return false;
            const u32 loop_reset=operation==MusicBufferFillOperation::Full?1:0;if(!reset_fill_stream(object,loop_reset,0,host,result))return false;if(signed_word(result)<0)return true;
            if(!read_fill_stream(object,lock.first+total,lock.bytes-total,count,host,result))return false;if(signed_word(result)<0)return true;total+=count;
        }}else if(!silence_fill(object,lock.first+total,lock.bytes-total,host))return false;
    }
    u32 ignored=0;if(!host.unlock_music_data(buffer,lock,ignored))return false;result=0;return true;
}
}

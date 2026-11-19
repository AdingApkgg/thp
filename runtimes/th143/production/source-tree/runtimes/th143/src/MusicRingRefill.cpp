#include "MusicRingRefill.hpp"
namespace th143 {
static bool ring_buffer(AnmView object,MusicRingRefillHost& host,u32& token){AnmView array{nullptr};if(!host.music_fill_region(object.get(4),4,array)||!array.data)return false;token=array.get(0);return true;}
static bool ring_stream(AnmView object,MusicRingRefillHost& host,AnmView& stream){return host.music_fill_region(object.get(12),0xa0,stream)&&stream.data;}
bool refill_music_ring(AnmView object,u32 bytes,u8 critical,u8& nesting,const MusicRingScratch& scratch,u32 query_output_token,MusicRingRefillHost& host,u32& result){
    if(!object.data||bytes<0xa0)return false;if(!object.get(4)||!object.get(12)){result=0x800401f0;return true;}
    if(critical){if(!host.enter_music_ring())return false;++nesting;}
    auto finish=[&](u32 hr){if(critical){if(!host.leave_music_ring())return false;--nesting;}result=hr;return true;};
    u32 buffer=0;if(!ring_buffer(object,host,buffer)||!buffer)return false;u32 play=scratch.first_play,write=scratch.first_write,hr=0;
    if(!host.music_ring_positions(buffer,true,play,true,write,hr))return false;
    if(object.get(0x88)>=write-object.get(0x94)&&object.get(0x88)<write)return finish(0x800401f0);
    if(!ring_buffer(object,host,buffer))return false;if(!buffer)return finish(0x800401f0);
    u32 restored=0;if(!query_music_buffer_restore(buffer,true,query_output_token,restored,host,hr))return false;if(signed_word(hr)<0)return finish(hr);
    if(restored){if(!ring_buffer(object,host,buffer)||!fill_music_buffer(object,bytes,buffer,0,0,MusicBufferFillOperation::Full,0,host,hr))return false;return finish(hr);}
    MusicRingLock lock;lock.first_bytes=scratch.lock_first_bytes;lock.second_bytes=scratch.lock_second_bytes;
    if(!ring_buffer(object,host,buffer)||!host.lock_music_ring(buffer,object.get(0x88),object.get(0x94),lock,hr))return false;if(signed_word(hr)<0)return finish(hr);
    //The native split-region branch returns before Unlock and before leaving
    //the critical section. Preserve its held-lock and nesting side effects.
    if(lock.second){result=0x8000ffff;return true;}
    AnmView stream{nullptr},meta{nullptr};
    if(!object.get(0x90)){
        if(!ring_stream(object,host,stream))return false;u32 count=0;if(!read_music_stream(stream,lock.first,lock.first_bytes,true,count,host,hr))return false;if(signed_word(hr)<0)return finish(hr);
        u32 filled=count;if(filled<lock.first_bytes){if(!ring_stream(object,host,stream))return false;stream.put(0x9c,1);}
        for(u32 attempts=0;filled<lock.first_bytes;++attempts){
            if(attempts>=1000000)return false;if(!ring_stream(object,host,stream)||!host.music_fill_region(stream.get(0x90),0x34,meta)||!meta.data)return false;
            if(!reset_music_stream(stream,meta,1,0,host.music_fill_file_base(),host,hr))return false;if(signed_word(hr)<0)return finish(hr);
            if(!ring_stream(object,host,stream)||!read_music_stream(stream,lock.first+filled,lock.first_bytes-filled,true,count,host,hr))return false;if(signed_word(hr)<0)return finish(hr);filled+=count;
        }
    }else{
        if(!ring_stream(object,host,stream)||!host.music_fill_region(stream.get(0x90),0x34,meta)||!meta.data)return false;std::uint16_t bits;std::memcpy(&bits,meta.data+0x2e,2);
        if(!host.fill_music_bytes(lock.first,bits==8?128:0,lock.first_bytes))return false;
    }
    if(!ring_buffer(object,host,buffer)||!host.unlock_music_data(buffer,{lock.first,lock.first_bytes},hr))return false;
    play=scratch.second_play;write=0;if(!ring_buffer(object,host,buffer)||!host.music_ring_positions(buffer,true,play,false,write,hr))return false;if(signed_word(hr)<0)return finish(hr);
    const u32 old=object.get(0x80),size=object.get(8);if(!size)return false;
    object.put(0x84,object.get(0x84)+(play<old?size-old+play:play-old));const u32 next=(object.get(0x88)+lock.first_bytes)%size;
    object.put(0x80,play);object.put(0x88,next);return finish(0);
}
}

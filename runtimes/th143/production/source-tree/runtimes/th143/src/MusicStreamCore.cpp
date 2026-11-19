#include "MusicStreamCore.hpp"
namespace th143 {
bool configure_music_memory(AnmView s,u32 data,u32 bytes,u32 metadata,u32,u32& result){
    if(!s.data)return false;s.put(0x90,metadata);s.put(0x88,bytes);s.put(0x80,data);s.put(0x84,data);s.put(0x7c,1);result=0x80004001;return true;
}
bool reset_music_stream(AnmView s,AnmView meta,u32 loop,u32 position,u32 file_base,MusicStreamHost& host,u32& result){
    if(!s.data)return false;
    if(s.get(0x7c)){
        if(!meta.data)return false;const u32 data=s.get(0x80);s.put(0x84,data);const u32 length=meta.get(0x1c);if(signed_word(length)>0)s.put(0x88,length);
        const u32 start=meta.get(0x18);if(u8(loop)&&signed_word(start)>0)s.put(0x84,data+start);result=0;return true;
    }
    const u32 handle=s.get(0x8c);if(!handle||handle==0xffffffff){result=0x800401f0;return true;}if(!meta.data)return false;
    const u32 start=meta.get(0x18),length=meta.get(0x1c),base=meta.get(0x10)+file_base;
    if(u8(loop)&&signed_word(start)>0){if(!host.seek_music_stream(handle,base+start))return false;s.put(8,length-start);result=0;return true;}
    if(position>=length)position+=start-length;
    if(!host.seek_music_stream(handle,base+position))return false;s.put(8,length-position);result=0;return true;
}
bool read_music_stream(AnmView s,u32 destination,u32 bytes,bool count_present,u32& count,MusicStreamHost& host,u32& result){
    if(!s.data)return false;
    if(s.get(0x7c)){
        const u32 cursor=s.get(0x84);if(!cursor){result=0x800401f0;return true;}if(count_present)count=0;
        const u32 base=s.get(0x80),length=s.get(0x88);u32 n=bytes;if(cursor+n>base+length)n=base-cursor+length;
        if(!host.copy_music_bytes(destination,cursor,n))return false;s.put(0x84,cursor+n);if(count_present)count=n;result=0;return true;
    }
    const u32 handle=s.get(0x8c);if(!handle){result=0x800401f0;return true;}
    if(!destination||!count_present){result=0x80070057;return true;}
    const u32 left=s.get(8),n=bytes>left?left:bytes;s.put(8,left-n);
    // Native passes its destination-argument slot as lpNumberOfBytesRead.
    // Preserve that slot's initial value if a declared service leaves it alone.
    u32 actual=destination;if(!host.read_music_stream_file(handle,destination,n,actual))return false;count=actual;result=0;return true;
}
bool close_music_stream(AnmView s,MusicStreamHost& host,u32& result){
    if(!s.data)return false;if(s.get(0x78)==1){if(!host.close_music_stream_file(s.get(0x8c)))return false;s.put(0x8c,0xffffffff);}result=0;return true;
}
}

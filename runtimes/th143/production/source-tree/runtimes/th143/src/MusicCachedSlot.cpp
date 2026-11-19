#include "MusicCachedSlot.hpp"
namespace th143 {
bool start_cached_music_slot(AnmView audio,u32 bytes,u32 slot,u8 enabled,u8 flags,u32 parameter,MusicCachedSlotHost& host,u32& result){
    if(!audio.data||bytes<0x57b0)return false;if(!audio.get(12)||!enabled||!audio.get(0)){result=0xffffffff;return true;}if(slot>=16)return false;
    const u32 path_offset=0x4678+slot*256;if(!(flags&0x10))return host.queue_cached_music_path(0x53b1e0+path_offset,result);
    if(!audio.get(0x18bc+slot*4)){result=0xffffffff;return true;}
    for(u32 at=0;;++at){const u32 source=path_offset+at,destination=0x1984+at;if(source>=bytes||destination>=bytes)return false;const u8 c=audio.data[source];audio.data[destination]=c;if(!c)break;}
    AnmView metadata{nullptr};if(!host.cached_music_metadata(audio.get(0x187c+slot*4),metadata)||!metadata.data)return false;std::uint16_t alignment;std::memcpy(&alignment,metadata.data+0x2c,2);if(!alignment)return false;
    u32 segment=metadata.get(0x24)*u32(alignment);segment<<=2;segment>>=3;
    u32 handle=0;if(!host.create_cached_music_event(handle))return false;audio.put(0x5780,handle);
    if(!host.create_cached_music_thread(0x473700,parameter,audio,handle))return false;audio.put(0x14,handle);segment-=segment%alignment;
    const u8 algorithm[16]={};u32 hr=0;
    if(!host.initialize_cached_music(audio.get(12),audio,audio.get(0x18fc+slot*4),audio.get(0x193c+slot*4),audio.get(0x187c+slot*4),algorithm,segment,audio.get(0x5780),hr))return false;
    if(signed_word(hr)<0){result=0xffffffff;return true;}audio.put(0x197c,slot);result=0;return true;
}
}

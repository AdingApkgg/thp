#include "MusicArchiveInitialize.hpp"
namespace th143 {
bool initialize_music_archive(AnmView audio,u32 bytes,u32 parameter,MusicArchiveInitializeHost& host,u32& result){
    if(!audio.data||bytes<0x57b0)return false;std::memcpy(audio.data+0x5678,"thbgm.dat",10);
    if(!audio.get(12)||!audio.get(0)){result=0xffffffff;return true;}
    if(!host.teardown_archive_music(audio))return false;
    const u32 metadata=audio.get(0x1980);AnmView meta{nullptr};if(!host.archive_music_metadata(metadata,meta)||!meta.data)return false;
    std::uint16_t alignment;std::memcpy(&alignment,meta.data+0x2c,2);if(!alignment)return false;
    u32 segment=meta.get(0x24)*u32(alignment);segment<<=2;segment>>=3;
    u32 handle=0;if(!host.create_archive_music_event(handle))return false;audio.put(0x5780,handle);
    if(!host.create_archive_music_thread(0x473700,parameter,audio,handle))return false;audio.put(0x14,handle);segment-=segment%alignment;
    const u8 algorithm[16]={};u32 hr=0;if(!host.initialize_archive_music_object(audio.get(12),audio,metadata,algorithm,segment,audio.get(0x5780),hr))return false;
    result=signed_word(hr)<0?0xffffffffu:0;return true;
}
}

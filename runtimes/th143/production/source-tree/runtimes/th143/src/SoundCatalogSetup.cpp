#include "SoundCatalogSetup.hpp"
#include <cstring>
namespace th143 {
bool prepare_sound_catalog(AnmView audio,u32 audio_bytes,const u8* table,u32 table_bytes,u32 table_token){
    if(!audio.data||audio_bytes<0x57b0||!table)return false;
    for(u32 id=0;id<88;++id){
        AnmView voice=audio.sub(0x1a84+id*24);voice.put(4,0xffffffff);u32 at=0;
        for(;;at+=20){if(at>table_bytes||table_bytes-at<20)return false;u32 key;std::memcpy(&key,table+at,4);if(key==id)break;}
        voice.put(12,id);voice.put(8,table_token+at);
    }
    for(u32 i=0;i<12;++i)audio.put(0x1c+i*4,0xffffffff);return true;
}
}

#include "SoundArchivePreload.hpp"
namespace th143 {
bool preload_sound_archive(AnmView audio,u32 audio_bytes,const char* const* names,u32 name_count,SoundArchivePreloadHost& host){
    if(!audio.data||audio_bytes<0x57b0||!names||name_count<77)return false;
    for(u32 i=0;i<77;++i){
        if(audio.get(0x5798)==2)return true;u32 token=0;
        if(!host.read_sound_file(names[i],token))return false;audio.put(0x22c4+i*4,token);
        if(!token)return host.log_sound_file_failure(names[i]);
    }
    while(!audio.get(0x5798))if(!host.wait_sound_preload(1,audio))return false;
    return true;
}
}

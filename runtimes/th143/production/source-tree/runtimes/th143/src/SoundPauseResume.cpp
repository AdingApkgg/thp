#include "SoundPauseResume.hpp"
namespace th143 {
bool pause_sound_bank(AnmView audio,u32 bytes,u32 status,SoundQueuePumpHost& host){
    if(!audio.data||bytes<0x57b0)return false;audio.put(0x1c,0xffffffff);
    for(u32 i=0;i<88;++i){const u32 at=0x1a84+i*24;audio.put(at+20,0);const u32 buffer=audio.get(at);if(!buffer)continue;
        u32 ignored=0;if(!host.query_sound_status(buffer,status,ignored))return false;audio.put(at+20,status&1);if(!host.sound_voice_call(audio.get(at),0x48,nullptr,0,ignored))return false;}
    return true;
}
bool resume_sound_bank(AnmView audio,u32 bytes,SoundQueuePumpHost& host){
    if(!audio.data||bytes<0x57b0)return false;
    for(u32 i=0;i<88;++i){const u32 at=0x1a84+i*24,buffer=audio.get(at);if(!buffer||!audio.get(at+20))continue;const u8* descriptor=nullptr;if(!host.sound_descriptor(audio.get(at+8),descriptor)||!descriptor)return false;
        u32 flags=0;std::memcpy(&flags,descriptor+12,4);const u32 args[]={0,0,flags};u32 ignored=0;if(!host.sound_voice_call(buffer,0x30,args,3,ignored))return false;}
    return true;
}
}

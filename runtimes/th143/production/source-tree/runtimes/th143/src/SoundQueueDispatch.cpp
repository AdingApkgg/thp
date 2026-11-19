#include "SoundQueueDispatch.hpp"
namespace th143 {
bool dispatch_sound_queue(AnmView audio,u32 audio_bytes,u8 enabled,u32 status,SoundQueuePumpHost& host,u32& result){
    if(!audio.data||audio_bytes<0x57b0)return false;
    if(!audio.get(12)){result=0;return true;}
    u32 hr=0;
    if(enabled)for(u32 slot=0;slot<12;++slot){
        const u32 id=audio.get(0x1c+slot*4);if(signed_word(id)<0)break;if(id>=88)return false;
        const u32 count=audio.get(0x4c+slot*4);audio.put(0x1c+slot*4,0xffffffff);AnmView voice=audio.sub(0x1a84+id*24);
        if(signed_word(count)<0){
            voice.put(20,0);if(const u32 token=voice.get(0)){if(!host.query_sound_status(token,status,hr))return false;voice.put(20,status&1);if(!host.sound_voice_call(token,0x48,nullptr,0,hr))return false;}
            audio.put(0x4c+slot*4,0);continue;
        }
        if(count>128)return false;u32 sum=0;for(u32 i=0;i<count;++i)sum+=audio.get(0x7c+slot*512+i*4);
        const u32 pan=count?u32(signed_word(sum)/i32(count)):0;audio.put(0x4c+slot*4,0);
        const u8* descriptor=nullptr;if(voice.get(0)&&(!host.sound_descriptor(voice.get(8),descriptor)||!descriptor))return false;
        if(!start_sound_voice(voice,{const_cast<u8*>(descriptor)},pan,audio.get(0x57a8),host,hr))return false;
    }
    result=audio.get(0x24f8);return true;
}
}

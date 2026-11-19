#include "SoundVoiceLoad.hpp"
#include <cstring>
namespace th143 {
bool load_sound_voice(AnmView audio,u32 audio_bytes,u32 voice_index,const char* name,SoundVoiceLoadHost& host,u32& result){
    if(!audio.data||audio_bytes<0x57b0||voice_index>=88)return false;
    if(!audio.get(12)){result=0;return true;}
    AnmView voice=audio.sub(0x1a84+voice_index*24);u32 hr=0;
    if(voice.get(0)){if(!host.release_sound_buffer(voice.get(0),hr))return false;voice.put(0,0);}
    auto file_index=[&](AnmView v,u32& index){const u8* descriptor=nullptr;if(!host.sound_descriptor(v.get(8),descriptor)||!descriptor)return false;std::memcpy(&index,descriptor+4,4);return index<88;};
    const i32 previous=signed_word(voice.get(12));if(previous>88)return false;
    if(previous>0){u32 wanted=0;if(!file_index(voice,wanted))return false;for(i32 i=0;i<previous;++i){const AnmView prior=audio.sub(0x1a84+u32(i)*24);u32 index=0;if(!file_index(prior,index))return false;if(index==wanted){if(!host.duplicate_sound_buffer(audio.get(0),prior.get(0),voice,hr))return false;result=0;return true;}}}
    u32 index=0;if(!file_index(voice,index))return false;
    while(!audio.get(0x22c4+index*4)){
        if(!host.wait_sound_resource(10,audio))return false;
        if(audio.get(0x5798)==2){result=0;return true;}
        if(!file_index(voice,index))return false;
    }
    if(!file_index(voice,index))return false;const u32 resource=audio.get(0x22c4+index*4);const u8* raw=nullptr;u32 mapped=0;
    if(!host.sound_resource(resource,raw,mapped))return false;
    auto cleanup=[&](){u32 live=0;if(!file_index(voice,live))return false;const u32 token=audio.get(0x22c4+live*4);if(token){if(!host.free_sound_resource(token))return false;audio.put(0x22c4+live*4,0);}return true;};
    SoundWavePcm pcm;const auto status=read_sound_wave_pcm(raw,mapped,pcm);
    if(status==SoundWavePcmStatus::Unavailable)return false;
    if(status==SoundWavePcmStatus::Invalid){if(!host.log_sound_wave(std::memcmp(raw,"RIFF",4)?0:1,name)||!cleanup())return false;result=0xffffffff;return true;}
    if(!host.create_sound_buffer(audio.get(0),0x80c8,pcm.bytes,pcm.format,voice,hr))return false;
    if(signed_word(hr)<0){if(!cleanup())return false;result=0xffffffff;return true;}
    SoundVoiceLock lock;if(!host.lock_sound_buffer(voice.get(0),pcm.bytes,lock,hr))return false;
    if(signed_word(hr)<0){if(!cleanup())return false;result=0xffffffff;return true;}
    if(!host.copy_sound_bytes(lock.first,resource+pcm.offset,lock.first_bytes))return false;
    if(lock.second_bytes&&!host.copy_sound_bytes(lock.second,resource+pcm.offset+lock.first_bytes,lock.second_bytes))return false;
    if(!host.unlock_sound_buffer(voice.get(0),lock,hr)||!cleanup()||!host.log_sound_wave(2,name))return false;
    result=0;return true;
}
}

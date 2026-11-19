#include "MusicVolume.hpp"
namespace th143 {
bool set_music_volume(u32 buffer,u32 base,u32 volume,SoundVoiceStartHost& host,u32& result){
    u32 attenuation=0xffffd8f0;
    if(volume){
        float normalized=float(signed_word(volume));normalized/=100.f;
        float curve=1.f-normalized;curve*=curve;curve=1.f-curve;
        curve*=float(signed_word(base+5000u));
        const u32 scaled=curve>=-2147483648.f&&curve<2147483648.f?u32(i32(curve)):0x80000000u;
        attenuation=scaled-5000u;
    }
    return host.sound_voice_call(buffer,0x3c,&attenuation,1,result);
}
}

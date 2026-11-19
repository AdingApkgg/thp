#include "SoundReload.hpp"
namespace th143 {
bool reload_sound_settings(AnmView audio,u32 bytes,u8 music,u8 sound,SoundReloadHost& host,u32& result){
    if(!audio.data||bytes<0x57b0)return false;for(u32 i=0;i<12;++i)audio.put(0x1c+i*4,0xffffffff);
    if(audio.get(0x578c)){
        if(!audio.get(0x5798))audio.put(0x5798,1);u32 status=0;
        if(!host.wait_sound_worker(audio.get(0x578c),100,status))return false;
        for(u32 steps=0;status==0x102;++steps){if(steps==1000000||!host.sleep_sound_worker(1)||!host.wait_sound_worker(audio.get(0x578c),100,status))return false;}
        if(!host.wait_sound_worker(audio.get(0x5790),100,status))return false;
        for(u32 steps=0;status==0x102;++steps){if(steps==1000000||!host.sleep_sound_worker(1)||!host.wait_sound_worker(audio.get(0x5790),100,status))return false;}
        if(!host.close_sound_worker(audio.get(0x578c))||!host.close_sound_worker(audio.get(0x5790)))return false;audio.put(0x578c,0);audio.put(0x5790,0);
    }
    if(!audio.get(12)){result=0xffffffff;return true;}if(!audio.get(0)){result=0;return true;}
    const i32 music_value=std::int8_t(music),sound_value=std::int8_t(sound);audio.put(0x57a4,u32(music_value));audio.put(0x57a8,u32(sound_value));
    u32 attenuation=0xffffd8f0;if(sound_value){float normalized=float(music_value);normalized/=100.f;float curve=1.f-normalized;curve*=curve;curve*=curve;curve=1.f-curve;curve*=-5000.f;const u32 scaled=curve>=-2147483648.f&&curve<2147483648.f?u32(i32(curve)):0x80000000u;attenuation=0xffffec78u-scaled;}
    audio.put(0x57ac,attenuation);result=0;return true;
}
}

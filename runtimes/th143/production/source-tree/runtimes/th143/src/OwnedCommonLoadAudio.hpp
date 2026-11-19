#pragma once
#include "CommonLoadAudio.hpp"
#include "OwnedMusicArchiveInitialize.hpp"
#include "SoundReload.hpp"
namespace th143 {
struct OwnedCommonLoadAudio:CommonLoadAudioServices {
    OwnedMusicControllerMainHost& music;SoundReloadHost& workers;u8 music_volume=100,sound_volume=100;
    OwnedCommonLoadAudio(OwnedMusicControllerMainHost& music,SoundReloadHost& workers):music(music),workers(workers){}
    bool reload_common_audio(AnmView audio,u32& result)override{return reload_sound_settings(audio,0x57b0,music_volume,sound_volume,workers,result);}
    bool initialize_common_archive(AnmView audio,u32& result)override{return initialize_owned_music_archive(audio,0x57b0,music,result);}
};
}

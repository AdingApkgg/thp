#pragma once
#include "OwnedMusicMemoryPlatformV3.hpp"
#include "SoundDeviceBankRuntime.hpp"
namespace th143 {
//Concrete prototype combining the independently compared device/bank and
//owned BGM platforms. Cooperative preload order and caller clock are explicit;
//real worker overlap, native OS/device timing and full CommonLoad remain open.
struct OwnedAudioDevicePlatformV2:OwnedMusicMemoryPlatformV3 {
    SoundDeviceBankRuntime device;u32 window=0x7002c000;
    explicit OwnedAudioDevicePlatformV2(AnmView audio):OwnedMusicMemoryPlatformV3(audio),device(bank){}
    void reset(){OwnedMusicMemoryPlatformV3::reset();device.reset();}
    bool music_region(u32 token,u32 bytes,AnmView& out)override{if(token==SoundDeviceBankRuntime::wrapper_token)return device.sound_initialize_region(token,bytes,out);return OwnedMusicMemoryPlatformV3::music_region(token,bytes,out);}
    bool prepare(){
        if(prepared)return true;if(!bank.audio.data||bank.audio.get(0x5778)||metadata.size()<520||bank.catalog.size()!=1760||bank.waves.size()!=77||device.filenames.size()!=77)return false;
        if(!device.preload()||!device.initialize(window,0x7001efe4)||device.result)return false;
        bank.audio.put(0x1980,metadata_token);bank.audio.put(0x5788,archive_file_base);std::memcpy(bank.audio.data+0x5678,"thbgm.dat",10);prepared=true;return true;
    }
};
}

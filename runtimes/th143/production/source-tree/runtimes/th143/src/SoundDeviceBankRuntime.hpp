#pragma once
#include "SoundDeviceInitialize.hpp"
#include "SoundBankRuntime.hpp"
#include <algorithm>
namespace th143 {
//Concrete finite CPU platform for device initialization plus the actual77
//resource slots/88voice loaders. Device/primary/silent services model an
//available driver; real hardware clocks and asynchronous workers remain open.
struct SoundDeviceBankRuntime:SoundDeviceInitializeHost {
    static constexpr u32 wrapper_token=0x73600000,primary_token=0x73601000,silent_token=0x73602000,silent_sample=0x73700000;
    SoundBankRuntime& bank;std::vector<u32> filenames;std::vector<u8> wrapper=std::vector<u8>(4),silent_pcm=std::vector<u8>(0x8000);bool wrapper_live=false;u32 device_ref=0,primary_ref=0,silent_ref=0,silent_locked=0,silent_playing=0,timer_window=0,result=0;
    explicit SoundDeviceBankRuntime(SoundBankRuntime& bank):bank(bank){}
    void reset(){wrapper.assign(4,0);silent_pcm.assign(0x8000,0);wrapper_live=false;device_ref=primary_ref=silent_ref=silent_locked=silent_playing=timer_window=result=0;}
    bool preload(){std::vector<const char*> names;for(const auto& wave:bank.waves)names.push_back(wave.name.c_str());return preload_sound_archive(bank.audio,0x57b0,names.data(),names.size(),bank);}
    bool initialize(u32 window,u32 format_token){if(bank.catalog.size()!=1760||bank.waves.size()!=77||filenames.size()!=77)return false;return initialize_sound_device(bank.audio,0x57b0,bank.catalog.data(),bank.catalog.size(),filenames.data(),filenames.size(),window,format_token,*this,result);}
    bool allocate_sound_wrapper(u32 bytes,u32& token)override{if(bytes!=4||wrapper_live)return false;token=wrapper_token;wrapper.assign(4,0);wrapper_live=true;bank.event(0x400,{bytes,token});return true;}
    bool sound_initialize_region(u32 token,u32 bytes,AnmView& out)override{if(token!=wrapper_token||bytes>4||!wrapper_live)return false;out={wrapper.data()};return true;}
    bool create_sound_device(u32 token,u32& device,u32& hr)override{if(token!=wrapper_token)return false;device=SoundBankRuntime::device;AnmView{wrapper.data()}.put(0,device);device_ref=1;hr=0;bank.event(0x401,{0,token,0,device,hr});return true;}
    bool cooperative_sound_device(u32 device,u32 window,u32 level,u32& hr)override{if(device!=SoundBankRuntime::device)return false;hr=0;bank.event(0x402,{device,window,level,hr});return true;}
    bool release_sound_device(u32 device,u32& remaining)override{if(device!=SoundBankRuntime::device)return false;remaining=0;device_ref=0;bank.event(0x40d,{device,remaining});return true;}
    bool free_sound_wrapper(u32 token)override{if(token!=wrapper_token||!wrapper_live)return false;wrapper_live=false;bank.event(0x40e,{token});return true;}
    bool create_primary_sound_buffer(u32 device,const u8* descriptor,u32& buffer,u32& hr)override{if(device!=SoundBankRuntime::device)return false;buffer=primary_token;primary_ref=1;hr=0;bank.event(0x403,{device,buffer,hr},descriptor,36);return true;}
    bool format_primary_sound_buffer(u32 buffer,const u8* format,u32& hr)override{if(buffer!=primary_token||!primary_ref)return false;hr=0;bank.event(0x404,{buffer,hr},format,18);return true;}
    bool release_primary_sound_buffer(u32 buffer,u32& remaining)override{if(buffer!=primary_token||!primary_ref)return false;remaining=0;primary_ref=0;bank.event(0x405,{buffer,remaining});return true;}
    bool create_silent_sound_buffer(u32 device,const u8* descriptor,const u8* format,AnmView audio,u32& hr)override{if(device!=SoundBankRuntime::device)return false;audio.put(4,silent_token);silent_pcm.assign(0x8000,0xcd);silent_ref=1;hr=0;u8 payload[54];std::memcpy(payload,descriptor,36);std::memcpy(payload+36,format,18);bank.event(0x406,{device,silent_token,hr},payload,54);return true;}
    bool lock_silent_sound_buffer(u32 buffer,SoundDeviceLock& lock,u32& hr)override{if(buffer!=silent_token||!silent_ref)return false;lock={silent_sample,0x8000,0,0};silent_locked=1;hr=0;bank.event(0x407,{buffer,0,0x8000,lock.first,lock.first_bytes,0,0,0,hr});return true;}
    bool zero_silent_sound_bytes(u32 destination,u32 bytes)override{if(destination!=silent_sample||bytes!=silent_pcm.size())return false;bank.event(0x408,{destination,0,bytes});std::memset(silent_pcm.data(),0,bytes);return true;}
    bool unlock_silent_sound_buffer(u32 buffer,const SoundDeviceLock& lock,u32& hr)override{if(buffer!=silent_token)return false;silent_locked=0;hr=0;bank.event(0x409,{buffer,lock.first,lock.first_bytes,lock.second,lock.second_bytes,hr});return true;}
    bool play_silent_sound_buffer(u32 buffer,u32& hr)override{if(buffer!=silent_token)return false;silent_playing=1;hr=0;bank.event(0x40a,{buffer,0,0,1,hr});return true;}
    bool install_sound_timer(u32 window,u32 id,u32 milliseconds,u32 callback)override{timer_window=window;bank.event(0x40b,{window,id,milliseconds,callback,0});return true;}
    bool sound_initialize_abort(u32& value)override{value=bank.audio.get(0x5798);return true;}
    bool initialize_device_voice(u32 index,AnmView,u32 filename,u32& hr)override{const auto it=std::find(filenames.begin(),filenames.end(),filename);if(it==filenames.end())return false;const u32 file=u32(it-filenames.begin());return load_sound_voice(bank.audio,0x57b0,index,bank.waves[file].name.c_str(),bank,hr);}
    bool log_sound_initialize(u32 format,u32 filename)override{bank.event(0x40c,{format,filename});return true;}
};
}

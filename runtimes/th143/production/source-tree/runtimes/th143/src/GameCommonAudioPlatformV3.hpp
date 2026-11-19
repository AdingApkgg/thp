#pragma once
#include "OwnedAudioDevicePlatformV2.hpp"
#include "SoundWorkerLifecycle.hpp"
#include "SoundArchiveWorkerStart.hpp"
#include "AnmResourceWorld.hpp"
namespace th143 {
//Explicit cooperative scheduler: CommonLoad's settings reload changes abort0
//to1 before waiting; the first wait completes preload and device workers in
//that order. No actual OS delay/concurrent mutation is claimed by this host.
struct GameCommonAudioPlatformV3:OwnedAudioDevicePlatformV2,SoundWorkerLifecycleHost,SoundArchiveWorkerStartHost {
    AnmResourceWorld* resources=nullptr;bool workers_started=false,archive_registered=false,preload_done=false,device_done=false,device_closed=false,archive_closed=false;
    static constexpr u32 device_handle=0x6d400000,device_id=0x6d410000,archive_handle=0x6d420000;
    explicit GameCommonAudioPlatformV3(AnmView audio):OwnedAudioDevicePlatformV2(audio){}
    void reset(){OwnedAudioDevicePlatformV2::reset();workers_started=archive_registered=preload_done=device_done=device_closed=archive_closed=false;}
    bool music_region(u32 token,u32 bytes,AnmView& out)override{if(OwnedAudioDevicePlatformV2::music_region(token,bytes,out))return true;if(resources)for(auto& region:resources->regions)if(token>=region.token&&std::uint64_t(token)+bytes<=std::uint64_t(region.token)+region.bytes.size()){out={region.bytes.data()+token-region.token};return true;}return false;}
    bool music_track_table(u32 token,const u8*& out,u32& bytes)override{if(OwnedAudioDevicePlatformV2::music_track_table(token,out,bytes))return true;if(resources)for(auto& region:resources->regions)if(token>=region.token&&token-region.token<region.bytes.size()){out=region.bytes.data()+token-region.token;bytes=region.bytes.size()-(token-region.token);return true;}return false;}
    bool start_workers(){if(workers_started||bank.waves.size()!=77||bank.catalog.size()!=1760||device.filenames.size()!=77)return false;u32 ignored=0;if(!run_sound_worker_lifecycle(bank.audio,0x57b0,SoundWorkerOperation::Construct,window,*this,ignored))return false;workers_started=true;return true;}
    bool prepare(){return prepared;}
    bool zero_sound_owner(AnmView audio,u32 bytes)override{bank.event(0x500,{0x53b1e0,0,bytes});std::memset(audio.data,0,bytes);return true;}
    bool create_sound_device_worker(u32 entry,u32 parameter,AnmView audio,u32& handle)override{if(entry!=0x471ed0||parameter!=0x53b1e0)return false;audio.put(0x5794,device_id);handle=device_handle;bank.event(0x501,{entry,parameter,handle,device_id});return true;}
    bool create_sound_archive_worker(u32 entry,u32 parameter,u32& handle)override{if(entry!=0x4721f0||parameter!=0x53b1e0||archive_registered)return false;archive_registered=true;handle=archive_handle;bank.event(0x502,{entry,parameter,handle});return true;}
    bool initialize_worker_sound_device(u32 window,AnmView,u32& result)override{if(!device.initialize(window,0x7001efdc))return false;result=device.result;return true;}
    bool wait_sound_worker(u32 handle,u32 milliseconds,u32& status)override{
        if(!workers_started||!archive_registered||milliseconds!=100||(handle!=device_handle&&handle!=archive_handle&&handle!=0))return false;
        if(!handle){status=0xffffffff;bank.event(0x503,{handle,milliseconds,status});return true;}
        if(!preload_done){if(bank.audio.get(0x5798)==0||!device.preload())return false;preload_done=true;}
        if(!device_done){u32 ignored=0;if(!run_sound_worker_lifecycle(bank.audio,0x57b0,SoundWorkerOperation::DeviceWorker,0,*this,ignored))return false;device_done=true;prepared=device.result==0;}
        status=0;bank.event(0x503,{handle,milliseconds,status});return true;
    }
    bool sleep_sound_worker(u32)override{return false;}
    bool close_sound_worker(u32 handle)override{const bool valid=handle==device_handle||handle==archive_handle;if(handle==device_handle)device_closed=true;if(handle==archive_handle)archive_closed=true;bank.event(0x504,{handle,valid?1u:0u});return true;}
    bool close_music_file(u32 handle)override{const u32 valid=file_positions.erase(handle)?1:0;bank.event(0x304,{handle,valid});return true;}
};
}

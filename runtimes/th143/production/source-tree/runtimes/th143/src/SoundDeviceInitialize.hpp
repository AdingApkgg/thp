#pragma once
#include "SoundPrimaryFormat.hpp"
#include "SoundCatalogSetup.hpp"
namespace th143 {
struct SoundDeviceLock {u32 first=0,first_bytes=0,second=0,second_bytes=0;};
struct SoundDeviceInitializeHost:SoundPrimaryFormatHost {
    virtual bool allocate_sound_wrapper(u32 bytes,u32& token)=0;
    virtual bool sound_initialize_region(u32 token,u32 bytes,AnmView&)=0;
    virtual bool create_sound_device(u32 wrapper,u32& device,u32& result)=0;
    virtual bool cooperative_sound_device(u32 device,u32 window,u32 level,u32& result)=0;
    virtual bool release_sound_device(u32 device,u32& remaining)=0;
    virtual bool free_sound_wrapper(u32 wrapper)=0;
    virtual bool create_silent_sound_buffer(u32 device,const u8* descriptor,const u8* format,AnmView audio,u32& result)=0;
    virtual bool lock_silent_sound_buffer(u32 buffer,SoundDeviceLock&,u32& result)=0;
    virtual bool zero_silent_sound_bytes(u32 destination,u32 bytes)=0;
    virtual bool unlock_silent_sound_buffer(u32 buffer,const SoundDeviceLock&,u32& result)=0;
    virtual bool play_silent_sound_buffer(u32 buffer,u32& result)=0;
    virtual bool install_sound_timer(u32 window,u32 id,u32 milliseconds,u32 callback)=0;
    virtual bool sound_initialize_abort(u32& value)=0;
    virtual bool initialize_device_voice(u32 index,AnmView voice,u32 filename,u32& result)=0;
    virtual bool log_sound_initialize(u32 format,u32 filename)=0;
};
//471f10. Filename tokens follow raw catalog row order; voice descriptors use
//the ID lookup from the separately verified initialization prefix. The caller
//declares the logical stack format token and successful Lock output domain.
bool initialize_sound_device(AnmView audio,u32 bytes,const u8* catalog,u32 catalog_bytes,
                              const u32* filenames,u32 filename_count,u32 window,u32 format_token,
                              SoundDeviceInitializeHost&,u32& result);
}

#pragma once
#include "SoundWavePcm.hpp"
#include "AnmState.hpp"
namespace th143 {
struct SoundVoiceLock {u32 first=0,first_bytes=0,second=0,second_bytes=0;};
struct SoundVoiceLoadHost {
    virtual ~SoundVoiceLoadHost()=default;
    virtual bool sound_descriptor(u32 token,const u8*& data)=0; // read-only20bytes
    virtual bool sound_resource(u32 token,const u8*& data,u32& mapped_bytes)=0;
    virtual bool wait_sound_resource(u32 milliseconds,AnmView audio)=0;
    virtual bool release_sound_buffer(u32 token,u32& hresult)=0;
    virtual bool duplicate_sound_buffer(u32 device,u32 source,AnmView destination,u32& hresult)=0;
    virtual bool create_sound_buffer(u32 device,u32 flags,u32 bytes,const u8* format,AnmView destination,u32& hresult)=0;
    virtual bool lock_sound_buffer(u32 buffer,u32 bytes,SoundVoiceLock&,u32& hresult)=0;
    virtual bool copy_sound_bytes(u32 destination,u32 source,u32 bytes)=0;
    virtual bool unlock_sound_buffer(u32 buffer,const SoundVoiceLock&,u32& hresult)=0;
    virtual bool free_sound_resource(u32 token)=0;
    virtual bool log_sound_wave(u32 kind,const char* name)=0; //0badRIFF,1badWAVE,2loaded
};
//473440. Bounded88-entry voice/cache domain within the declared57b0 audio view.
bool load_sound_voice(AnmView audio,u32 audio_bytes,u32 voice_index,const char* name,
                      SoundVoiceLoadHost&,u32& result);
}

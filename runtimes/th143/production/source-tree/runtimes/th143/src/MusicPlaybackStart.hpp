#pragma once
#include "MusicOwnerReset.hpp"
#include "MusicBufferSelect.hpp"
#include "MusicVolume.hpp"
namespace th143 {
struct MusicPlaybackStartHost:MusicOwnerResetHost,MusicBufferSelectHost,SoundVoiceStartHost {
    bool music_select_region(u32 token,u32 bytes,AnmView& out)override{return music_fill_region(token,bytes,out);}
    bool music_select_status(u32 buffer,u32& status,u32& result)override{return music_buffer_status(buffer,status,result);}
    virtual bool music_start_clock(double& value)=0;
};
//4863a0; logical optional-output address is the caller's independently declared
// local slot (standalone entry ESP-12). Memory/file/driver services remain typed.
bool start_music_playback(AnmView object,u32 bytes,u32 priority,u32 flags,u32 position,
                          u32 volume,u32 output_token,MusicPlaybackStartHost&,u32& result);
}

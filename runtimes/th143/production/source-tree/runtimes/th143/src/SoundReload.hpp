#pragma once
#include "AnmState.hpp"
namespace th143 {
struct SoundReloadHost {
    virtual ~SoundReloadHost()=default;
    virtual bool wait_sound_worker(u32 handle,u32 milliseconds,u32& status)=0;
    virtual bool sleep_sound_worker(u32 milliseconds)=0;
    virtual bool close_sound_worker(u32 handle)=0;
};
//472a90 at the fixed global audio owner. Worker waits are explicit services.
bool reload_sound_settings(AnmView audio,u32 bytes,u8 music_volume,u8 sound_volume,
                           SoundReloadHost&,u32& result);
}

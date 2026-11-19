#pragma once
#include "SoundVoiceStart.hpp"
namespace th143 {
struct MusicPlaybackRelocateHost:SoundVoiceStartHost {
    virtual bool music_relocate_region(u32 token,u32 bytes,AnmView& out)=0;
    virtual bool music_relocate_call(u32 entry,u32 object,const u32* args,u32 count)=0;
};
//4870a0 single-thread domain. Helpers may change stream/metadata/buffer bindings;
// each subsequent original read resolves the current binding again.
bool relocate_music_playback(AnmView object,u32 bytes,u32 object_token,double time,
                             MusicPlaybackRelocateHost&);
}

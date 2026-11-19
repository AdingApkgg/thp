#pragma once
#include "MusicVolume.hpp"
namespace th143 {
struct MusicFrameHost:SoundVoiceStartHost {
    virtual bool music_frame_region(u32 token,u32 bytes,AnmView&)=0;
};
//Single4867b0/4867f0/486820/486850 operation is mode1/2/3/4 respectively.
//globals is an independent logical view: owner token0, music volume4.
bool advance_music_fade(AnmView object,u32 bytes,u32 mode,AnmView globals,
                        MusicFrameHost&,u32& completed);
//446920 re-reads the global owner before modes2,4,3, permitting callbacks to
//change the current object. Its incidental void return register is excluded.
bool update_music_frame(AnmView globals,u32 bytes,MusicFrameHost&);
}

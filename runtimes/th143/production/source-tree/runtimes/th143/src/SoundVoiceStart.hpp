#pragma once
#include "AnmState.hpp"
namespace th143 {
struct SoundVoiceStartHost {
 virtual ~SoundVoiceStartHost()=default;
 // Native DirectSound HRESULTs are deliberately ignored except for the last
 // return register; false means the platform call itself was unavailable.
 virtual bool sound_voice_call(u32 buffer,u32 method,const u32* args,u32 count,u32& hresult)=0;
};
//473380. Descriptor is the original20-byte sound table entry referenced at+8.
bool start_sound_voice(AnmView voice,AnmView descriptor,u32 pan,u32 volume,SoundVoiceStartHost&,u32& result);
}

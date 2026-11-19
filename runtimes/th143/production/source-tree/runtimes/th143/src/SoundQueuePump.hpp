#pragma once
#include "SoundVoiceStart.hpp"
namespace th143 {
struct SoundQueuePumpHost:SoundVoiceStartHost {
    virtual bool sound_descriptor(u32 token,const u8*& bytes)=0;
    virtual bool query_sound_status(u32 buffer,u32& status,u32& hresult)=0;
};
//472df0 SFX branch with no actionable music command (head outside1..9), in
// the single-thread domain. The initial caller scratch is the logical queue
// head pointer written at472e45; failed status services may preserve it.
bool pump_sound_queue(AnmView audio,u32 audio_bytes,u8 enabled,
                     SoundQueuePumpHost&,u32& result);
}

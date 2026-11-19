#pragma once
#include "SoundQueuePump.hpp"
namespace th143 {
// Fork of the verified SFX branch with its real caller-produced status scratch.
bool dispatch_sound_queue(AnmView audio,u32 audio_bytes,u8 enabled,u32 status_scratch,
                          SoundQueuePumpHost&,u32& result);
}

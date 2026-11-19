#pragma once
#include "SoundQueuePump.hpp"
namespace th143 {
//433f70 clears first pending ID, saves each buffer's playing bit, then stops.
//The initial query local is an independently declared caller scratch word;
//no-write GetStatus callbacks preserve it across successive voices.
bool pause_sound_bank(AnmView audio,u32 bytes,u32 status_seed,SoundQueuePumpHost&);
//448663..44868a voice loop; nonzero saved status resumes from current cursor
//with original descriptor flags. Other448640 menu/clock writes are outside it.
bool resume_sound_bank(AnmView audio,u32 bytes,SoundQueuePumpHost&);
}

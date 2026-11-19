#pragma once
#include "AnmState.hpp"
namespace th143 {
//472df0 with a declared silent wrapper, absent playback object, disabled
// streamed-BGM/file reads and disabled SFX device processing. Full audio owner
// storage includes the physical32nd queue sentinel and cached path bank.
bool pump_silent_music_owner(AnmView audio,bool streamed,bool playback,u8 music_enabled,u8 sound_enabled,u32& result);
}

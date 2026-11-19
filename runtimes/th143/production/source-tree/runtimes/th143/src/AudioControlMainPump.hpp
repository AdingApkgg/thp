#pragma once
#include "MusicControlPump.hpp"
#include "MusicPlaybackControl.hpp"
#include "SoundQueueDispatch.hpp"
namespace th143 {
struct AudioControlMainPumpHost:SoundQueuePumpHost,MusicPlaybackControlHost {};
// Single-thread472df0 composition for music5/6/7/8 or non-actionable heads.
// Uses the actual own playback/volume helpers, followed by the own SFX branch.
bool pump_audio_control_main(AnmView audio,u32 bytes,u8 music_enabled,u8 sound_enabled,
                             AudioControlMainPumpHost&,u32& result);
}

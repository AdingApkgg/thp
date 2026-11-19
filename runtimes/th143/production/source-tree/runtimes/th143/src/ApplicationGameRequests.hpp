#pragma once
#include "MusicCommandQueue.hpp"
namespace th143 {
//444810: rate and duration are literal IEEE f32 inputs. MXCSR exception flags
//are not part of this API; the integer queue argument and audio bytes are.
bool request_application_music_fade(AnmView audio,u32 duration_word,u32 rate_word,u32& result);
//44b7b0: mode is masked to the two mode bits, with unsigned shift wrapping.
bool initialize_application_game_mode(AnmView game,u32 mode,u32& result);
}

#pragma once
#include "SoundVoiceStart.hpp"
namespace th143 {
//486470, valid first-buffer domain. The BGM response curve is quadratic.
bool set_music_volume(u32 buffer,u32 base_attenuation,u32 global_volume,
                      SoundVoiceStartHost&,u32& result);
}

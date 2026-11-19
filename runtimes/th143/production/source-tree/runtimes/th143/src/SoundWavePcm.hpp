#pragma once
#include "SoundWaveChunk.hpp"
namespace th143 {
enum class SoundWavePcmStatus:u32 { Ready=0,Invalid=1,Unavailable=2 };
struct SoundWavePcm {u8 format[18]{};u32 offset=0,bytes=0;};
// RIFF/WAVE checks and fmt/data extraction from the 473440 voice loader.
// This preserves its literal eighteen-byte format copy, including PCM fmt16.
SoundWavePcmStatus read_sound_wave_pcm(const u8* data,u32 mapped_bytes,SoundWavePcm&);
}

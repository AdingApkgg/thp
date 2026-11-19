#include "SoundWavePcm.hpp"
#include <cstring>
namespace th143 {
SoundWavePcmStatus read_sound_wave_pcm(const u8* data,u32 mapped_bytes,SoundWavePcm& out){
    if(!data||mapped_bytes<12)return SoundWavePcmStatus::Unavailable;
    if(std::memcmp(data,"RIFF",4)||std::memcmp(data+8,"WAVE",4))return SoundWavePcmStatus::Invalid;
    u32 remaining;std::memcpy(&remaining,data+4,4);remaining-=12;
    u32 format_size=0,format_at=0;
    if(!find_sound_wave_chunk(data+12,mapped_bytes-12,reinterpret_cast<const u8*>("fmt "),remaining,format_size,format_at))return SoundWavePcmStatus::Unavailable;
    if(!format_at)return SoundWavePcmStatus::Invalid;
    format_at+=12;if(format_at>mapped_bytes||mapped_bytes-format_at<18)return SoundWavePcmStatus::Unavailable;
    u32 pcm_size=0,pcm_at=0;
    if(!find_sound_wave_chunk(data+12,mapped_bytes-12,reinterpret_cast<const u8*>("data"),remaining,pcm_size,pcm_at))return SoundWavePcmStatus::Unavailable;
    if(!pcm_at)return SoundWavePcmStatus::Invalid;
    pcm_at+=12;if(pcm_at>mapped_bytes||mapped_bytes-pcm_at<pcm_size)return SoundWavePcmStatus::Unavailable;
    std::memcpy(out.format,data+format_at,18);out.offset=pcm_at;out.bytes=pcm_size;
    return SoundWavePcmStatus::Ready;
}
}

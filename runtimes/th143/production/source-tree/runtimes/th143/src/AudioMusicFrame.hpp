#pragma once
#include "MusicFrame.hpp"
namespace th143 {
//446920 binding to the actual57b0-byte audio layout. The current owner and
//music volume are separated by0x2c bytes, so mirror the logical8byte view and
//refresh it after every physical buffer callback before the next fade phase.
bool update_audio_music_frame(AnmView audio,u32 bytes,MusicFrameHost&,u32& result);
}

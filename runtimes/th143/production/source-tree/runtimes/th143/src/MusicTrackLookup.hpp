#pragma once
#include "EclVm.hpp"
namespace th143 {
// 472420: first matching basename in the 0x34-byte music table; zero is also
// the native fallback when no name matches. false is an unavailable byte read.
bool find_music_track(const u8* table,u32 mapped_bytes,const char* path,
                      u32 path_bytes,u32& track);
}

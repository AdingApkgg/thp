#pragma once
#include "EclVm.hpp"
namespace th143 {
// 4723c0. The caller supplies mapped bytes separately from the original
// remaining-byte counter. false denotes a read outside that host boundary.
// A completed search returns payload_offset=0 when no tag was found.
bool find_sound_wave_chunk(const u8* data,u32 mapped_bytes,const u8* tag,
                          u32 remaining,u32& chunk_bytes,u32& payload_offset);
}

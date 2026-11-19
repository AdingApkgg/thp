#pragma once
#include "AnmState.hpp"
namespace th143 {
//471f10..471f70 prefix only: bind voice IDs to matching immutable descriptors
// and clear twelve request IDs. The following device allocation is separate.
bool prepare_sound_catalog(AnmView audio,u32 audio_bytes,const u8* table,
                          u32 table_bytes,u32 table_token);
}

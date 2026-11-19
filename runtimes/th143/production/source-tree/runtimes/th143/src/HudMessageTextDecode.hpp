#pragma once
#include "AnmState.hpp"
namespace th143 {
bool decode_hud_message_text(const u8* encoded,u32 available,u8* output,u32 capacity,u32& written);
}

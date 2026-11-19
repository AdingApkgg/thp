#pragma once
#include "AnmState.hpp"
namespace th143 {
// Original4672d0 skip and467310 copy. Input includes a readable sentinel
// after remaining bytes; an unterminated final line leaves destination intact.
bool skip_music_comment_line(const u8* source,u32 capacity,u32 offset,u32& remaining,u32& next);
bool copy_music_comment_line(u8* source,u32 capacity,u32 offset,u32& remaining,u8* destination,u32 destination_bytes,u32& next);
}

#pragma once
#include "MusicBufferFill.hpp"
namespace th143 {
struct MusicOwnerResetHost:MusicBufferFillHost {
    virtual bool position_music_buffer(u32 buffer,u32 position,u32& result)=0;
};
//486af0. The declared logical address of the caller's local optional-output
// slot is explicit; native standalone fixtures derive it from entry ESP-8.
bool reset_music_owner_buffer(AnmView object,u32 object_bytes,u32 position,
                              u32 status_output_token,MusicOwnerResetHost&,u32& result);
}

#pragma once
#include "AnmState.hpp"
namespace th143 {
struct SoundPrimaryFormatHost {
    virtual ~SoundPrimaryFormatHost()=default;
    virtual bool create_primary_sound_buffer(u32 device,const u8* descriptor,u32& buffer,u32& result)=0;
    virtual bool format_primary_sound_buffer(u32 buffer,const u8* format,u32& result)=0;
    virtual bool release_primary_sound_buffer(u32 buffer,u32& remaining)=0;
};
//485280, all three caller ABI words are unused. Failure after creation retains
//the primary interface as original; physical driver services remain explicit.
bool configure_primary_sound_format(AnmView wrapper,u32 bytes,SoundPrimaryFormatHost&,u32& result);
}

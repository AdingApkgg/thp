#pragma once
#include "MusicBufferRestore.hpp"
#include "MusicStreamCore.hpp"
namespace th143 {
struct MusicBufferLock {u32 first=0,bytes=0;};
struct MusicBufferFillHost:MusicBufferRestoreHost,MusicStreamHost {
    virtual bool music_fill_region(u32 token,u32 bytes,AnmView& out)=0;
    virtual u32 music_fill_file_base()const=0;
    virtual bool lock_music_data(u32 buffer,u32 requested,MusicBufferLock&,u32& result)=0;
    virtual bool unlock_music_data(u32 buffer,const MusicBufferLock&,u32& result)=0;
    virtual bool fill_music_bytes(u32 destination,u8 value,u32 bytes)=0;
};
enum class MusicBufferFillOperation:u32 {Full,ExplicitBytes};
//485f70 full owner+8 size (loop reset1),4860e0 explicit size (loop reset0).
// The original uses only the first Lock region and can leave a failed fill locked.
bool fill_music_buffer(AnmView object,u32 object_bytes,u32 buffer,u32 loop,
                       u32 position,MusicBufferFillOperation,u32 explicit_bytes,
                       MusicBufferFillHost&,u32& result);
}

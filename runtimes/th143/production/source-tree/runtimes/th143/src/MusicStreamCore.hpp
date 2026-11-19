#pragma once
#include "AnmState.hpp"
namespace th143 {
// The compared state is a declared 0xa0-byte prefix, not an assertion about
// the complete native allocation. Addresses remain logical host tokens.
struct MusicStreamHost {
    virtual ~MusicStreamHost()=default;
    virtual bool copy_music_bytes(u32 destination,u32 source,u32 bytes)=0;
    virtual bool seek_music_stream(u32 handle,u32 offset)=0;
    virtual bool read_music_stream_file(u32 handle,u32 destination,u32 bytes,u32& actual)=0;
    virtual bool close_music_stream_file(u32 handle)=0;
};
bool configure_music_memory(AnmView,u32 data,u32 bytes,u32 metadata,u32 unused,u32& result); //486d60
bool reset_music_stream(AnmView,AnmView metadata,u32 loop,u32 position,u32 file_base,MusicStreamHost&,u32& result); //486db0
bool read_music_stream(AnmView,u32 destination,u32 bytes,bool count_present,u32& count,MusicStreamHost&,u32& result); //486eb0
bool close_music_stream(AnmView,MusicStreamHost&,u32& result); //486f80
}

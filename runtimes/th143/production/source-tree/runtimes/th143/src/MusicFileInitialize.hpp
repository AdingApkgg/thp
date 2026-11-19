#pragma once
#include "MusicMemoryInitialize.hpp"
#include "MusicFileOpen.hpp"
namespace th143 {
struct MusicFileInitializeHost:MusicMemoryInitializeHost,MusicFileOpenHost {
    virtual bool free_music_initialize_stream(u32 token)=0;
};
//485360 regular file-backed owner initialization. Fixed native path token
//4c6034("thbgm.dat"); unused ABI padding and faulting/throwing allocations
//are excluded. Shares the derived owner construction with485710.
bool initialize_file_music(u32 wrapper,u32& output,u32 metadata,const u8* algorithm_guid,
                            u32 segment,u32 event,u32 file_base,MusicFileInitializeHost&,u32& result);
}

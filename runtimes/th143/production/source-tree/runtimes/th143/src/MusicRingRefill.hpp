#pragma once
#include "MusicBufferFill.hpp"
namespace th143 {
struct MusicRingLock {u32 first=0,first_bytes=0,second=0,second_bytes=0;};
struct MusicRingScratch {u32 first_play=0,first_write=0,second_play=0,lock_first_bytes=0,lock_second_bytes=0;};
struct MusicRingRefillHost:MusicBufferFillHost {
    virtual bool music_ring_positions(u32 buffer,bool play_present,u32& play,bool write_present,u32& write,u32& result)=0;
    virtual bool lock_music_ring(u32 buffer,u32 offset,u32 bytes,MusicRingLock&,u32& result)=0;
    virtual bool enter_music_ring()=0;
    virtual bool leave_music_ring()=0;
};
//486890. Standalone caller declares scratch seeds and the logical optional
//output pointer; notification argument is unused in the regular native path.
bool refill_music_ring(AnmView object,u32 bytes,u8 critical,u8& nesting,
                        const MusicRingScratch&,u32 query_output_token,
                        MusicRingRefillHost&,u32& result);
}

#pragma once
#include "EclVm.hpp"
namespace th143 {
struct MusicBufferRestoreHost {
    virtual ~MusicBufferRestoreHost()=default;
    virtual bool music_buffer_status(u32 buffer,u32& status,u32& result)=0;
    virtual bool restore_music_buffer(u32 buffer,u32& result)=0;
    virtual bool sleep_music_restore(u32 milliseconds)=0;
};
// Common original restore loop: two Restore calls per iteration, sleeping only
// when the first call returns DSERR_BUFFERLOST. A nonzero second result retries.
bool restore_lost_music_buffer(u32 buffer,MusicBufferRestoreHost&);
//486250. output_token is the caller's declared logical optional-output address;
// GetStatus uses the original argument slot as scratch, not a zero seed.
bool query_music_buffer_restore(u32 buffer,bool output_present,u32 output_token,
                                u32& restored,MusicBufferRestoreHost&,u32& result);
}

#pragma once
#include "MusicTrackLookup.hpp"
#include "AnmState.hpp"
namespace th143 {
struct MusicPcmPreloadHost {
    virtual ~MusicPcmPreloadHost()=default;
    virtual bool free_music_cache(u32)=0;
    virtual bool open_music_file(const char*,u32 access,u32 share,u32 creation,u32 flags,u32& handle)=0;
    virtual bool seek_music_file(u32 handle,u32 offset)=0;
    virtual bool allocate_music_cache(u32 bytes,u32& token)=0;
    virtual bool read_music_file(u32 handle,u32 token,u32 bytes)=0;
    virtual bool close_music_file(u32 handle)=0;
    virtual bool music_load_progress(u32)=0;
    virtual bool music_load_error(const char*)=0;
};
// 4726a0, single-thread domain. Host bools mean the service was available;
// the original ignores Seek/Read/Close OS return values. Zero allocation and
// INVALID_HANDLE_VALUE remain distinct results from unavailable services.
bool preload_music_pcm(AnmView audio,u32 audio_bytes,const u8* table,u32 table_bytes,
                       u32 slot,const char* name,u32 name_bytes,u8 flags,
                       MusicPcmPreloadHost&,u32& result);
}

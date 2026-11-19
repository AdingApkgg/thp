#pragma once
#include "AnmState.hpp"
namespace th143 {
struct MusicCachedSlotHost {
    virtual ~MusicCachedSlotHost()=default;
    virtual bool cached_music_metadata(u32 token,AnmView& metadata)=0;
    virtual bool queue_cached_music_path(u32 path,u32& result)=0;
    virtual bool create_cached_music_event(u32& handle)=0;
    virtual bool create_cached_music_thread(u32 entry,u32 parameter,AnmView audio,u32& handle)=0;
    virtual bool initialize_cached_music(u32 wrapper,AnmView audio,u32 data,u32 bytes,
                                        u32 metadata,const u8* algorithm,u32 segment,
                                        u32 event,u32& result)=0;
};
//472880, sixteen-slot domain and nonzero block alignment. Ignored485710 ABI
// padding is outside this typed service interface; it is not synthesized.
bool start_cached_music_slot(AnmView audio,u32 bytes,u32 slot,u8 music_enabled,
                             u8 flags,u32 thread_parameter,MusicCachedSlotHost&,u32& result);
}

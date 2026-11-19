#pragma once
#include "AnmState.hpp"
namespace th143 {
struct MusicArchiveInitializeHost {
    virtual ~MusicArchiveInitializeHost()=default;
    virtual bool teardown_archive_music(AnmView audio)=0;
    virtual bool archive_music_metadata(u32 token,AnmView&)=0;
    virtual bool create_archive_music_event(u32& handle)=0;
    virtual bool create_archive_music_thread(u32 entry,u32 parameter,AnmView audio,u32& handle)=0;
    virtual bool initialize_archive_music_object(u32 wrapper,AnmView audio,u32 metadata,
                                                const u8* algorithm,u32 segment,u32 event,u32& result)=0;
};
//472560. The sole caller ABI word is unused. The thread parameter comes from
//4e4828. Teardown and the file factory are explicit composition boundaries.
bool initialize_music_archive(AnmView audio,u32 bytes,u32 thread_parameter,
                              MusicArchiveInitializeHost&,u32& result);
}

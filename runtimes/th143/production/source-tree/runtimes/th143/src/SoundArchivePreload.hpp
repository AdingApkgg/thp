#pragma once
#include "AnmState.hpp"
namespace th143 {
struct SoundArchivePreloadHost {
    virtual ~SoundArchivePreloadHost()=default;
    virtual bool read_sound_file(const char* name,u32& token)=0;
    virtual bool wait_sound_preload(u32 milliseconds,AnmView audio)=0;
    virtual bool log_sound_file_failure(const char* name)=0;
};
//4721f0 worker body; the host owns resource bytes and cooperative waiting.
// There are77 filename/cache slots (76 distinct names), independently of88voices.
bool preload_sound_archive(AnmView audio,u32 audio_bytes,const char* const* names,
                           u32 name_count,SoundArchivePreloadHost&);
}

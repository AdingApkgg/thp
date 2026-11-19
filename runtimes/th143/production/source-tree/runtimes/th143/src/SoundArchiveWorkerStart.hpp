#pragma once
#include "AnmState.hpp"
namespace th143 {
struct SoundArchiveWorkerStartHost {
    virtual ~SoundArchiveWorkerStartHost()=default;
    virtual bool create_sound_archive_worker(u32 entry,u32 parameter,u32& handle)=0;
};
//472260. CreateThread's local thread-ID output is unused after the call.
inline bool start_sound_archive_worker(AnmView audio,u32 bytes,SoundArchiveWorkerStartHost& host,u32& result){if(!audio.data||bytes<0x57b0)return false;u32 handle=0;if(!host.create_sound_archive_worker(0x4721f0,0x53b1e0,handle))return false;audio.put(0x5790,handle);result=handle;return true;}
}

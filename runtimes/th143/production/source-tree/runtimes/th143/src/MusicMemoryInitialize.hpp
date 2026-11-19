#pragma once
#include "MusicOwnerConstruct.hpp"
namespace th143 {
struct MusicMemoryInitializeHost:MusicOwnerConstructHost {
    virtual bool allocate_music_initialize_object(u32 bytes,u32& token)=0;
    virtual bool allocate_music_initialize_notify(u32 bytes,u32& token)=0;
    virtual bool free_music_initialize_notify(u32 token)=0;
    virtual bool create_memory_music_buffer(u32 device,const u8* descriptor,u32& buffer,u32& result)=0;
    virtual bool query_memory_music_notify(u32 buffer,u32& notify,u32& result)=0;
    virtual bool set_memory_music_notifications(u32 notify,u32 count,u32 table,u32& result)=0;
    virtual bool release_memory_music_notify(u32 notify,u32& remaining)=0;
};
//485710 regular path. The distinct output cell is represented by reference.
//Unused ABI padding arguments4/9, allocation exceptions and null object
//allocations which fault before returning are outside this typed operation.
bool initialize_memory_music(u32 wrapper,u32& output,u32 data,u32 data_bytes,
                             u32 metadata,const u8* algorithm_guid,u32 segment,
                             u32 event,MusicMemoryInitializeHost&,u32& result);
}

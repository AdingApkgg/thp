#pragma once
#include "AnmState.hpp"
namespace th143 {
struct MusicMetadataLoadHost {
    virtual ~MusicMetadataLoadHost()=default;
    virtual bool music_metadata_region(u32 token,u32 bytes,AnmView& out)=0;
    virtual bool allocate_music_metadata(u32 bytes,u32& token)=0;
    virtual bool free_music_metadata(u32 token)=0;
    virtual bool release_music_interface(u32 token,u32& remaining)=0;
    virtual bool create_metadata_buffer(u32 device,const u8* descriptor,u32 output_slot,u32& result)=0;
    virtual bool query_metadata_notify(u32 buffer,u32& notify,u32& result)=0;
    virtual bool set_metadata_notifications(u32 notify,u32 count,u32 table,u32& result)=0;
};
//485c90. Uses a local36-byte descriptor copy with only lpwfxFormat replaced.
// Partial allocations/COM outputs are deliberately retained on native failures.
bool load_music_metadata(AnmView object,u32 bytes,u32 metadata,MusicMetadataLoadHost&,u32& result);
}

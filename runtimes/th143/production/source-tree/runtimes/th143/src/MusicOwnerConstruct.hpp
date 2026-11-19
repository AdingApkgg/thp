#pragma once
#include "MusicOwnerReset.hpp"
namespace th143 {
struct MusicOwnerConstructHost:MusicOwnerResetHost {
    virtual bool allocate_music_owner_array(u32 bytes,u32& token)=0;
};
//485a70 typed regular constructor, distinct nonaliasing input buffer-reference
// cell represented by its value; its unused third ABI word is not synthesized.
bool construct_music_owner(AnmView object,u32 bytes,u32 object_token,u32 buffer,
                            u32 buffer_bytes,u32 stream,MusicOwnerConstructHost&,u32& result);
//486710 derived memory owner: leaves+8c untouched while zeroing80/84/88/90.
bool construct_memory_music_owner(AnmView object,u32 bytes,u32 object_token,u32 buffer,
                                   u32 buffer_bytes,u32 stream,u32 segment,
                                   MusicOwnerConstructHost&,u32& result);
}

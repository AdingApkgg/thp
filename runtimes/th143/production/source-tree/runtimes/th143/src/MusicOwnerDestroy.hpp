#pragma once
#include "AnmState.hpp"
namespace th143 {
struct MusicOwnerDestroyHost {
    virtual ~MusicOwnerDestroyHost()=default;
    virtual bool music_destroy_region(u32 token,u32 bytes,AnmView&)=0;
    virtual bool release_destroyed_music_buffer(u32 token,u32& remaining)=0;
    virtual bool free_music_owner_array(u32 token)=0;
    virtual bool free_music_owner_object(u32 token)=0;
    virtual bool close_destroyed_music_file(u32 handle)=0;
};
//485ef0 plus485c60/486770 deleting and4867a0 nondeleting wrappers.
//variant0=base body,1=base deleting,2=derived deleting,3=derived body.
//The base body's incidental EAX is not a defined portable result.
bool destroy_music_owner(AnmView object,u32 bytes,u32 token,u32 variant,u32 flags,
                         MusicOwnerDestroyHost&,u32& result);
}

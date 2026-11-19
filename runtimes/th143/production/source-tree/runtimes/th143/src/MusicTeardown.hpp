#pragma once
#include "MusicPlaybackControl.hpp"
namespace th143 {
struct MusicTeardownHost:MusicPlaybackControlHost {
    virtual bool post_music_thread_quit(u32 thread_id)=0;
    virtual bool wait_music_thread(u32 handle,u32 milliseconds,u32& status)=0;
    virtual bool close_music_thread(u32 handle)=0;
    virtual bool delete_music_object(u32 token,u32 flags)=0;
    virtual bool start_cached_music(u32 object,u32& result)=0;
};
bool teardown_music(AnmView audio,u32 bytes,MusicTeardownHost&); //4729f0
bool begin_cached_music(AnmView audio,u32 bytes,u32 value,MusicTeardownHost&,u32& result); //4729b0
}

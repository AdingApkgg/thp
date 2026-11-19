#pragma once
#include "AnmState.hpp"
namespace th143 {
struct MusicPlaybackControlHost {
    virtual ~MusicPlaybackControlHost()=default;
    virtual bool music_region(u32 token,u32 bytes,AnmView& out)=0;
    virtual bool music_buffer_call(u32 buffer,u32 method,const u32* args,u32 count,u32& result)=0;
    virtual bool music_buffer_status(u32 buffer,u32& status,u32& result)=0;
    virtual bool music_clock(double& value)=0;
    virtual bool music_file_position(u32 handle,u32& value)=0;
    virtual bool music_file_close(u32 handle)=0;
    virtual bool music_stream_reopen(u32 stream,u32 metadata,u32 offset)=0;
};
// Original486330/4864f0/486570/486600/486670/4866b0.
enum class MusicPlaybackOperation:u32 {FirstBuffer,Stop,Pause,Resume,Rewind,AnyPlaying};
bool music_playback_control(AnmView object,u32 object_bytes,MusicPlaybackOperation,
                            u32 close_file,MusicPlaybackControlHost&,u32& result);
}

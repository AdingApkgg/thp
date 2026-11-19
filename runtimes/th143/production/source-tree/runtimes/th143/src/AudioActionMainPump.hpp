#pragma once
#include "AudioTrackMainPump.hpp"
#include "MusicCachedSlot.hpp"
#include "MusicTeardown.hpp"
#include "MusicFileOpen.hpp"
#include "MusicPcmPreload.hpp"
namespace th143 {
struct AudioActionMainPumpHost:AudioTrackMainPumpHost,MusicCachedSlotHost,MusicTeardownHost,MusicFileOpenHost,MusicPcmPreloadHost {
    virtual bool music_region(u32 token,u32 bytes,AnmView& out)override=0;
    virtual bool music_buffer_call(u32 buffer,u32 method,const u32* args,u32 count,u32& result)override=0;
    virtual bool music_buffer_status(u32 buffer,u32& status,u32& result)override=0;
    virtual bool music_clock(double& value)override=0;
    virtual bool music_file_position(u32 handle,u32& value)override=0;
    virtual bool music_file_close(u32 handle)override=0;
    virtual u32 music_file_base()const=0;
    virtual u32 music_thread_parameter()const=0;
    // Remaining buffer-fill/load/play controller internals are explicit services.
    virtual bool music_action_call(u32 entry,u32 object,const u32* args,u32 count,u32& result)=0;
    bool music_relocate_call(u32 entry,u32 object,const u32* args,u32 count)override{u32 ignored=0;return music_action_call(entry,object,args,count,ignored);}
    bool cached_music_metadata(u32 token,AnmView& out)override{return music_region(token,0x34,out);}
    bool start_cached_music(u32 object,u32& result)override{const u32 args[]={0,1,0};return music_action_call(0x4863a0,object,args,3,result);}
    bool music_stream_reopen(u32 token,u32 metadata,u32 position)override;
};
//472df0 single-thread main pump, with own preload/cached-start/stop/teardown,
// control/track helpers and SFX dispatch. A repeated preload may only reach a
// non-actionable sentinel; malformed active32nd entries remain unavailable.
bool pump_audio_action_main(AnmView audio,u32 bytes,u8 music_enabled,u8 sound_enabled,
                            u8 flags,AudioActionMainPumpHost&,u32& result);
}

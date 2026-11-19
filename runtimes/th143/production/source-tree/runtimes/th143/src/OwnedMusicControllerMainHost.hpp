#pragma once
#include "AudioActionMainPump.hpp"
#include "MusicPlaybackStart.hpp"
#include "MusicMetadataLoad.hpp"
#include "MusicFileInitialize.hpp"
#include "MusicQueuedPath.hpp"
#include "MusicOwnerDestroy.hpp"
#include "MusicFrame.hpp"
namespace th143 {
//Prototype composition adapter. Physical memory, files, buffers, allocation,
//COM references, thread APIs and caller-stack provenance remain mandatory
//platform services; game controller bodies below execute the own modules.
struct OwnedMusicControllerMainHost:AudioActionMainPumpHost,MusicPlaybackStartHost,
                                   MusicMetadataLoadHost,MusicFileInitializeHost,
                                   MusicOwnerDestroyHost,MusicFrameHost {
    virtual AnmView owned_music_audio()=0;
    virtual bool owned_music_query_output(u32 entry,u32& logical_token)=0;
    virtual bool sound_voice_call(u32,u32,const u32*,u32,u32&)override=0;
    virtual bool music_buffer_status(u32,u32&,u32&)override=0;
    bool music_fill_region(u32 token,u32 bytes,AnmView& out)final{return music_region(token,bytes,out);}
    bool music_metadata_region(u32 token,u32 bytes,AnmView& out)final{return music_region(token,bytes,out);}
    bool music_destroy_region(u32 token,u32 bytes,AnmView& out)final{return music_region(token,bytes,out);}
    bool music_frame_region(u32 token,u32 bytes,AnmView& out)final{return music_region(token,bytes,out);}
    bool music_relocate_region(u32 token,u32 bytes,AnmView& out)final{return music_region(token,bytes,out);}
    u32 music_fill_file_base()const final{return music_file_base();}
    bool music_start_clock(double& value)final{return music_clock(value);}
    bool music_buffer_call(u32 token,u32 method,const u32* args,u32 count,u32& hr)override{return sound_voice_call(token,method,args,count,hr);}
    bool position_music_buffer(u32 token,u32 position,u32& hr)final{return music_buffer_call(token,0x34,&position,1,hr);}
    bool music_action_call(u32 entry,u32 token,const u32* args,u32 count,u32& result)final;
    bool initialize_cached_music(u32 wrapper,AnmView audio,u32 data,u32 bytes,u32 metadata,
                                  const u8* algorithm,u32 segment,u32 event,u32& result)final;
    bool initialize_file_owned_music(u32 wrapper,u32& output,u32 metadata,
                                      const u8* algorithm,u32 segment,u32 event,u32& result);
    bool queue_cached_music_path(u32 path,u32& result)final;
    bool delete_music_object(u32 token,u32 flags)final;
};
}

#include "OwnedMusicControllerMainHost.hpp"
namespace th143 {
bool OwnedMusicControllerMainHost::music_action_call(u32 entry,u32 token,const u32* args,u32 count,u32& result){
    AnmView object{nullptr};if(!music_region(token,0xa0,object)||!object.data)return false;
    auto& start=static_cast<MusicPlaybackStartHost&>(*this);u32 output=0;
    if(entry==0x485c90&&count==1)return load_music_metadata(object,0xa0,args[0],*this,result);
    if(entry==0x485f70&&count==3)return fill_music_buffer(object,0xa0,args[0],args[1],args[2],MusicBufferFillOperation::Full,0,start,result);
    if(entry==0x486af0&&count==1){if(!owned_music_query_output(entry,output))return false;return reset_music_owner_buffer(object,0xa0,args[0],output,start,result);}
    if(entry==0x4863a0&&count==3){if(!owned_music_query_output(entry,output))return false;const AnmView audio=owned_music_audio();if(!audio.data)return false;return start_music_playback(object,0xa0,args[0],args[1],args[2],audio.get(0x57a4),output,start,result);}
    return false;
}
bool OwnedMusicControllerMainHost::initialize_cached_music(u32 wrapper,AnmView audio,u32 data,u32 bytes,u32 metadata,const u8* algorithm,u32 segment,u32 event,u32& result){
    if(!audio.data)return false;u32 output=audio.get(0x5778);if(!initialize_memory_music(wrapper,output,data,bytes,metadata,algorithm,segment,event,*this,result))return false;
    //485710 publishes only on successful completion. A physical callback may
    //have changed the external output cell on a failure; preserve that write.
    if(result==0)audio.put(0x5778,output);return true;
}
bool OwnedMusicControllerMainHost::delete_music_object(u32 token,u32 flags){
    AnmView object{nullptr};if(!music_region(token,0xa0,object)||!object.data)return false;const u32 table=object.get(0),variant=table==0x4c9b34?2:table==0x4c9b3c?1:0;
    if(!variant)return false;u32 ignored=0;return destroy_music_owner(object,0xa0,token,variant,flags,*this,ignored);
}
bool OwnedMusicControllerMainHost::initialize_file_owned_music(u32 wrapper,u32& output,u32 metadata,const u8* algorithm,u32 segment,u32 event,u32& result){return initialize_file_music(wrapper,output,metadata,algorithm,segment,event,music_file_base(),*this,result);}
bool OwnedMusicControllerMainHost::queue_cached_music_path(u32 path,u32& result){return queue_music_cached_path(owned_music_audio(),0x57b0,path,static_cast<AudioActionMainPumpHost&>(*this),result);}
}

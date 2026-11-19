#include "OwnedMusicArchiveInitialize.hpp"
namespace th143 {
namespace {
struct ArchiveHost:MusicArchiveInitializeHost {
    OwnedMusicControllerMainHost& host;explicit ArchiveHost(OwnedMusicControllerMainHost& host):host(host){}
    bool teardown_archive_music(AnmView audio)override{return teardown_music(audio,0x57b0,host);}
    bool archive_music_metadata(u32 token,AnmView& out)override{return host.music_region(token,0x34,out);}
    bool create_archive_music_event(u32& handle)override{return host.create_cached_music_event(handle);}
    bool create_archive_music_thread(u32 entry,u32 parameter,AnmView audio,u32& handle)override{return host.create_cached_music_thread(entry,parameter,audio,handle);}
    bool initialize_archive_music_object(u32 wrapper,AnmView audio,u32 metadata,const u8* algorithm,u32 segment,u32 event,u32& result)override{
        u32 output=audio.get(0x5778);if(!host.initialize_file_owned_music(wrapper,output,metadata,algorithm,segment,event,result))return false;
        if(result==0)audio.put(0x5778,output);return true;
    }
};
}
bool initialize_owned_music_archive(AnmView audio,u32 bytes,OwnedMusicControllerMainHost& host,u32& result){ArchiveHost adapter(host);return initialize_music_archive(audio,bytes,host.music_thread_parameter(),adapter,result);}
}

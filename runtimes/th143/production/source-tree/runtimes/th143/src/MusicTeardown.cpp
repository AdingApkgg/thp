#include "MusicTeardown.hpp"
namespace th143 {
bool teardown_music(AnmView audio,u32 bytes,MusicTeardownHost& host){
    if(!audio.data||bytes<0x57b0)return false;const u32 token=audio.get(0x5778);if(!token)return true;
    AnmView object{nullptr};if(!host.music_region(token,0xa0,object)||!object.data)return false;u32 ignored=0;if(!music_playback_control(object,0xa0,MusicPlaybackOperation::Stop,1,host,ignored))return false;
    if(audio.get(0x14)){
        if(!host.post_music_thread_quit(audio.get(0x10)))return false;u32 status=0;if(!host.wait_music_thread(audio.get(0x14),256,status))return false;
        for(u32 steps=0;status;++steps){if(steps==1000000||!host.post_music_thread_quit(audio.get(0x10))||!host.wait_music_thread(audio.get(0x14),256,status))return false;}
        if(!host.close_music_thread(audio.get(0x14))||!host.close_music_thread(audio.get(0x5780)))return false;audio.put(0x14,0);
    }
    if(const u32 current=audio.get(0x5778)){if(!host.delete_music_object(current,1))return false;audio.put(0x5778,0);}
    return true;
}
bool begin_cached_music(AnmView audio,u32 bytes,u32 value,MusicTeardownHost& host,u32& result){
    if(!audio.data||bytes<0x57b0)return false;const u32 token=audio.get(0x5778);if(!token){result=0xffffffff;return true;}u32 hr=0;if(!host.start_cached_music(token,hr))return false;
    if(signed_word(hr)<0){result=0xffffffff;return true;}audio.put(0x5784,value);result=0;return true;
}
}

#include "AudioControlMainPump.hpp"
#include "MusicVolume.hpp"
namespace th143 {
struct ControlAdapter:MusicControlPumpHost {
    AnmView audio;AudioControlMainPumpHost& host;
    ControlAdapter(AnmView a,AudioControlMainPumpHost& h):audio(a),host(h){}
    bool music_control_object(u32 token,AnmView& object,u32& bytes)override{bytes=0xa0;return host.music_region(token,bytes,object);}
    bool music_control_call(u32 entry,u32 token,const u32* args,u32 count)override{
        AnmView object{nullptr};if(!host.music_region(token,0xa0,object)||!object.data)return false;u32 result=0;
        if(entry==0x486470&&count==1){AnmView array{nullptr};if(!host.music_region(object.get(4),4,array)||!array.data)return false;return set_music_volume(array.get(0),args[0],audio.get(0x57a4),host,result);}
        if(!count&&(entry==0x486570||entry==0x486600))return music_playback_control(object,0xa0,entry==0x486570?MusicPlaybackOperation::Pause:MusicPlaybackOperation::Resume,0,host,result);
        return false;
    }
};
bool pump_audio_control_main(AnmView audio,u32 bytes,u8 music_enabled,u8 sound_enabled,AudioControlMainPumpHost& host,u32& result){
    if(!audio.data||bytes<0x57b0)return false;if(!audio.get(12)){result=0;return true;}
    const u32 command=audio.get(0x24f8);u32 scratch=0x53d6d8;
    if(command>=1&&command<=9){if(command<5||command>8)return false;ControlAdapter adapter(audio,host);bool reached=false;if(!pump_music_control(audio,bytes,music_enabled,adapter,reached,scratch)||!reached)return false;}
    return dispatch_sound_queue(audio,bytes,sound_enabled,scratch,host,result);
}
}

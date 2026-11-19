#include "MusicPlaybackStart.hpp"
namespace th143 {
static bool play_array(AnmView object,u32 index,MusicPlaybackStartHost& host,AnmView& array){if(index>=0x3fffffffu)return false;return host.music_fill_region(object.get(4),(index+1)*4,array)&&array.data;}
bool start_music_playback(AnmView object,u32 bytes,u32 priority,u32 flags,u32 position,u32 volume,u32 output_token,MusicPlaybackStartHost& host,u32& result){
    if(!object.data||bytes<0xa0||!output_token)return false;if(!object.get(4)){result=0x800401f0;return true;}
    u32 buffer=0;if(!select_music_buffer(object,bytes,host,buffer))return false;if(!buffer){result=0x80004005;return true;}
    u32 restored=0;if(!query_music_buffer_restore(buffer,true,output_token,restored,host,result))return false;if(signed_word(result)<0)return true;
    if(restored){if(!fill_music_buffer(object,bytes,buffer,0,position,MusicBufferFillOperation::Full,0,host,result))return false;if(signed_word(result)<0)return true;
        for(u32 i=0;i<object.get(0x10);++i){if(i==1000000)return false;AnmView array{nullptr};if(!play_array(object,i,host,array))return false;u32 ignored=0;if(!host.position_music_buffer(array.get(i*4),0,ignored))return false;}
    }
    for(u32 at=0x14;at<=0x1c;at+=4)object.put(at,0);
    AnmView first{nullptr};if(!play_array(object,0,host,first))return false;u32 ignored=0;if(!set_music_volume(first.get(0),0,volume,host,ignored))return false;
    object.put(0x50,1);object.put(0x20,priority);object.put(0x24,flags);object.put(0x2c,0);double clock;if(!host.music_start_clock(clock))return false;
    std::memcpy(object.data+0x30,&clock,8);std::memset(object.data+0x40,0,16);object.put(0x38,0);object.put(0x3c,0);
    const u32 args[]={0,priority,flags};return host.sound_voice_call(buffer,0x30,args,3,result);
}
}

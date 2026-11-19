#include "MusicFrame.hpp"
#include <initializer_list>
namespace th143 {
bool advance_music_fade(AnmView object,u32 bytes,u32 mode,AnmView globals,MusicFrameHost& host,u32& completed){
    if(!object.data||bytes<0xa0||!globals.data||mode<1||mode>4)return false;completed=0;if(object.get(0x1c)!=mode)return true;
    const u32 count=object.get(0x14)-1;object.put(0x14,count);u32 ignored=0;
    if(signed_word(count)<=0){object.put(0x1c,0);if(mode==1){AnmView array{nullptr};if(!host.music_frame_region(object.get(4),4,array)||!array.data)return false;if(!host.sound_voice_call(array.get(0),0x48,nullptr,0,ignored))return false;}completed=1;return true;}
    const u32 factor=mode==1?5000u:mode==2?u32(-5000):mode==3?u32(-1000):1000u;
    const i32 numerator=signed_word(count*factor),denominator=signed_word(object.get(0x18));if(!denominator)return false;
    const std::int64_t quotient=std::int64_t(numerator)/denominator;if(quotient<-2147483648LL||quotient>2147483647LL)return false;
    const u32 attenuation=u32(quotient)-(mode==1?5000u:mode==4?1000u:0u);AnmView array{nullptr};if(!host.music_frame_region(object.get(4),4,array)||!array.data)return false;
    return set_music_volume(array.get(0),attenuation,globals.get(4),host,ignored);
}
bool update_music_frame(AnmView globals,u32 bytes,MusicFrameHost& host){
    if(!globals.data||bytes<8)return false;if(!globals.get(0))return true;
    for(u32 mode:{1u,2u,4u,3u}){AnmView object{nullptr};if(!host.music_frame_region(globals.get(0),0xa0,object)||!object.data)return false;u32 ignored=0;if(!advance_music_fade(object,0xa0,mode,globals,host,ignored))return false;}
    return true;
}
}

#include "MusicPlaybackRelocate.hpp"
namespace th143 {
static u32 half(AnmView v,u32 at){std::uint16_t n;std::memcpy(&n,v.data+at,2);return n;}
bool relocate_music_playback(AnmView object,u32 bytes,u32 token,double time,MusicPlaybackRelocateHost& host){
    if(!object.data||bytes<0xa0)return false;AnmView array{nullptr},stream{nullptr},meta{nullptr};u32 ignored=0;
    if(!host.music_relocate_region(object.get(4),4,array)||!array.data||!host.sound_voice_call(array.get(0),0x48,nullptr,0,ignored))return false;
    if(!host.music_relocate_region(object.get(12),0xa0,stream)||!stream.data||!host.music_relocate_region(stream.get(0x90),0x34,meta)||!meta.data)return false;
    const u32 metadata_token=stream.get(0x90);double rate=double(signed_word(meta.get(0x24)));rate+=(meta.get(0x24)>>31)?4294967296.:0.;rate*=time;
    u32 offset=rate>=-2147483648.&&rate<2147483648.?u32(i32(rate)):0x80000000u;offset*=half(meta,0x2e)>>3;offset*=half(meta,0x22);offset-=half(meta,0x2c);
    if(!host.music_relocate_call(0x485c90,token,&metadata_token,1)||!host.music_relocate_call(0x486af0,token,&offset,1))return false;
    if(!host.music_relocate_region(object.get(12),0xa0,stream)||!stream.data)return false;stream.put(0x2c,stream.get(8));
    if(!host.music_relocate_region(stream.get(0x90),0x34,meta)||!meta.data||!host.music_relocate_region(object.get(4),4,array)||!array.data)return false;
    const u32 prepare[]={array.get(0),u32(meta.get(0x1c)!=0),offset};if(!host.music_relocate_call(0x485f70,token,prepare,3))return false;
    const u32 play[]={object.get(0x20),object.get(0x24),offset};if(!host.music_relocate_call(0x4863a0,token,play,3))return false;
    double origin;std::memcpy(&origin,object.data+0x30,8);origin-=time;std::memcpy(object.data+0x30,&origin,8);return true;
}
}

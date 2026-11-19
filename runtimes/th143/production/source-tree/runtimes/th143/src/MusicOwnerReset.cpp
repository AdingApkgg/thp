#include "MusicOwnerReset.hpp"
namespace th143 {
static bool reset_array(AnmView object,MusicOwnerResetHost& host,AnmView& array){return host.music_fill_region(object.get(4),4,array)&&array.data;}
bool reset_music_owner_buffer(AnmView object,u32 bytes,u32 position,u32 output_token,MusicOwnerResetHost& host,u32& result){
    if(!object.data||bytes<0xa0||!output_token)return false;AnmView array{nullptr};if(!reset_array(object,host,array))return false;
    const u32 buffer=array.get(0);if(!buffer||!object.get(12)){result=0x800401f0;return true;}
    for(u32 at=0x80;at<=0x90;at+=4)object.put(at,0);
    u32 restored=0;if(!query_music_buffer_restore(buffer,true,output_token,restored,host,result))return false;if(signed_word(result)<0)return true;
    if(restored){if(!reset_array(object,host,array)||!fill_music_buffer(object,bytes,array.get(0),0,position,MusicBufferFillOperation::Full,0,host,result))return false;if(signed_word(result)<0)return true;}
    AnmView stream{nullptr},metadata{nullptr};if(!host.music_fill_region(object.get(12),0xa0,stream)||!stream.data||!host.music_fill_region(stream.get(0x90),0x34,metadata)||!metadata.data)return false;
    u32 ignored=0;if(!reset_music_stream(stream,metadata,u32(stream.get(0x9c)==1),position,host.music_fill_file_base(),host,ignored))return false;
    if(!reset_array(object,host,array))return false;return host.position_music_buffer(array.get(0),0,result);
}
}

#include "SoundPrimaryFormat.hpp"
namespace th143 {
bool configure_primary_sound_format(AnmView wrapper,u32 bytes,SoundPrimaryFormatHost& host,u32& result){
    if(!wrapper.data||bytes<4)return false;const u32 device=wrapper.get(0);if(!device){result=0x800401f0;return true;}
    u8 descriptor[36]={};AnmView desc{descriptor};desc.put(0,36);desc.put(4,1);u32 buffer=0;if(!host.create_primary_sound_buffer(device,descriptor,buffer,result))return false;if(signed_word(result)<0)return true;
    const u8 format[18]={1,0,2,0,0x44,0xac,0,0,0x10,0xb1,2,0,4,0,16,0,0,0};
    if(!host.format_primary_sound_buffer(buffer,format,result))return false;if(signed_word(result)<0)return true;
    if(buffer){u32 ignored=0;if(!host.release_primary_sound_buffer(buffer,ignored))return false;}result=0;return true;
}
}

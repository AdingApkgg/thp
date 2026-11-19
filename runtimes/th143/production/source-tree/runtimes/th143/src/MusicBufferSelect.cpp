#include "MusicBufferSelect.hpp"
namespace th143 {
static bool select_array(AnmView object,u32 index,MusicBufferSelectHost& host,AnmView& array){if(index>=0x3fffffffu)return false;return host.music_select_region(object.get(4),(index+1)*4,array)&&array.data;}
bool select_music_buffer(AnmView object,u32 bytes,MusicBufferSelectHost& host,u32& buffer){
    if(!object.data||bytes<0xa0)return false;buffer=0;if(!object.get(4))return true;if(!object.get(0x10))return false;
    u32 index=0;AnmView array{nullptr};
    while(index<object.get(0x10)){if(index==1000000||!select_array(object,index,host,array))return false;const u32 token=array.get(index*4);
        if(token){u32 status=0,ignored=0;if(!host.music_select_status(token,status,ignored))return false;if(!(status&1))break;}++index;
    }
    if(index==object.get(0x10)){u32 value=0;if(!host.music_select_random(value)||!object.get(0x10))return false;index=value%object.get(0x10);}
    if(!select_array(object,index,host,array))return false;buffer=array.get(index*4);return true;
}
}

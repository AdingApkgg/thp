#include "MusicBufferRestore.hpp"
namespace th143 {
bool restore_lost_music_buffer(u32 buffer,MusicBufferRestoreHost& host){
    for(u32 steps=0;steps<1000000;++steps){u32 hr=0;if(!host.restore_music_buffer(buffer,hr))return false;if(hr==0x88780096&&!host.sleep_music_restore(10))return false;if(!host.restore_music_buffer(buffer,hr))return false;if(!hr)return true;}return false;
}
bool query_music_buffer_restore(u32 buffer,bool present,u32 token,u32& restored,MusicBufferRestoreHost& host,u32& result){
    if(present)restored=0;u32 status=present?token:0;if(!host.music_buffer_status(buffer,status,result))return false;if(signed_word(result)<0)return true;
    if(status&2){if(!restore_lost_music_buffer(buffer,host))return false;if(present)restored=1;result=0;}else result=1;return true;
}
}

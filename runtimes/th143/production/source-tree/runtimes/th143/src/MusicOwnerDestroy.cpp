#include "MusicOwnerDestroy.hpp"
namespace th143 {
bool destroy_music_owner(AnmView object,u32 bytes,u32 token,u32 variant,u32 flags,MusicOwnerDestroyHost& host,u32& result){
    if(!object.data||bytes<0xa0||variant>3)return false;
    if(variant>=2)object.put(0,0x4c9b34);object.put(0,0x4c9b3c);
    for(u32 i=0;i<object.get(0x10);++i){
        if(i>=1000000)return false;AnmView array{nullptr};if(!host.music_destroy_region(object.get(4),(i+1)*4,array)||!array.data)return false;
        if(const u32 buffer=array.get(i*4)){u32 ignored=0;if(!host.release_destroyed_music_buffer(buffer,ignored))return false;
            if(!host.music_destroy_region(object.get(4),(i+1)*4,array)||!array.data)return false;array.put(i*4,0);}
    }
    if(const u32 array=object.get(4)){if(!host.free_music_owner_array(array))return false;object.put(4,0);}
    if(const u32 stream=object.get(12)){AnmView s{nullptr};if(!host.music_destroy_region(stream,0xa0,s)||!s.data)return false;
        if(s.get(0x78)==1){if(!host.close_destroyed_music_file(s.get(0x8c)))return false;s.put(0x8c,0xffffffff);}
        if(!host.free_music_owner_object(stream))return false;object.put(12,0);
    }
    if(variant==1||variant==2){if((flags&1)&&!host.free_music_owner_object(token))return false;result=token;}
    return true;
}
}

#include "MusicMetadataLoad.hpp"
namespace th143 {
static bool metadata_array(AnmView object,u32 index,MusicMetadataLoadHost& host,AnmView& array){if(index>=0x3fffffffu)return false;return host.music_metadata_region(object.get(4),(index+1)*4,array)&&array.data;}
bool load_music_metadata(AnmView object,u32 bytes,u32 metadata,MusicMetadataLoadHost& host,u32& result){
    if(!object.data||bytes<0xa0)return false;object.put(0x50,0);
    for(u32 i=0;i<object.get(0x10);++i){if(i==1000000)return false;AnmView array{nullptr};if(!metadata_array(object,i,host,array))return false;
        if(const u32 token=array.get(i*4)){u32 ignored=0;if(!host.release_music_interface(token,ignored)||!metadata_array(object,i,host,array))return false;array.put(i*4,0);}
    }
    if(const u32 old=object.get(4)){if(!host.free_music_metadata(old))return false;object.put(4,0);}
    const u32 count=object.get(0x10),requested=count>0x3fffffffu?0xffffffffu:count*4;u32 table=0;if(!host.allocate_music_metadata(requested,table))return false;object.put(4,table);
    u8 descriptor[36];std::memcpy(descriptor,object.data+0x58,36);const u32 format=metadata+0x20;std::memcpy(descriptor+16,&format,4);u32 notify=0;
    for(u32 i=0;i<object.get(0x10);++i){
        if(i==1000000)return false;AnmView wrapper{nullptr};if(!host.music_metadata_region(object.get(0x7c),4,wrapper)||!wrapper.data)return false;u32 hr=0;
        if(!host.create_metadata_buffer(wrapper.get(0),descriptor,object.get(4)+i*4,hr))return false;if(signed_word(hr)<0){result=0x80004005;return true;}
        AnmView array{nullptr};if(!metadata_array(object,i,host,array)||!host.query_metadata_notify(array.get(i*4),notify,hr))return false;if(signed_word(hr)<0){result=0x80004005;return true;}
        u32 temporary=0;if(!host.allocate_music_metadata(64,temporary))return false;if(!temporary){result=0x8007000e;return true;}
        AnmView positions{nullptr};if(!host.music_metadata_region(temporary,64,positions)||!positions.data)return false;
        for(u32 j=0;j<8;++j){positions.put(j*8,object.get(0x94)*(j+1)-1);positions.put(j*8+4,object.get(0x98));}
        if(!host.set_metadata_notifications(notify,8,temporary,hr))return false;
        if(notify){u32 ignored=0;if(!host.release_music_interface(notify,ignored))return false;notify=0;}
        if(!host.free_music_metadata(temporary))return false;if(signed_word(hr)<0){result=0x80004005;return true;}
    }
    result=0;return true;
}
}

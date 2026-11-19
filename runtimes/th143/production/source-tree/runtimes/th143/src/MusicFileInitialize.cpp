#include "MusicFileInitialize.hpp"
namespace th143 {
bool initialize_file_music(u32 wrapper_token,u32& output,u32 metadata,const u8* guid,u32 segment,u32 event,u32 file_base,MusicFileInitializeHost& host,u32& result){
    AnmView wrapper{nullptr};if(!guid||!host.music_fill_region(wrapper_token,4,wrapper)||!wrapper.data)return false;
    if(!wrapper.get(0)){result=0x800401f0;return true;}
    u32 stream_token=0;if(!host.allocate_music_initialize_object(0xa0,stream_token))return false;AnmView stream{nullptr};if(!host.music_fill_region(stream_token,0xa0,stream)||!stream.data)return false;
    stream.put(0x90,0);stream.put(0,0);stream.put(0x2c,0);stream.put(0x7c,0);
    u32 ignored=0;stream.put(0x78,1);stream.put(0x7c,0);AnmView metadata_view{nullptr};if(!host.music_fill_region(metadata,0x34,metadata_view)||!metadata_view.data)return false;
    auto& file=static_cast<MusicFileOpenHost&>(host);if(!open_music_file(stream,0xa0,0x4c6034,metadata_view,metadata,0+file_base,file,ignored))return false;
    if(ignored!=0){if(stream.get(0x78)==1){if(!file.close_music_stream_file(stream.get(0x8c)))return false;stream.put(0x8c,0xffffffff);}if(!host.free_music_initialize_stream(stream_token))return false;result=0x80004005;return true;}
    u8 descriptor[36]={};AnmView desc{descriptor};desc.put(0,36);desc.put(4,0x18188);desc.put(8,segment*8);desc.put(16,stream.get(0x90)+0x20);std::memcpy(descriptor+20,guid,16);
    u32 buffer=0,notify=0,hr=0;if(!host.create_memory_music_buffer(wrapper.get(0),descriptor,buffer,hr))return false;if(signed_word(hr)<0){result=0x80004005;return true;}
    if(!host.query_memory_music_notify(buffer,notify,hr))return false;if(signed_word(hr)<0){result=0x80004005;return true;}
    u32 temporary=0;if(!host.allocate_music_initialize_notify(64,temporary))return false;if(!temporary){result=0x8007000e;return true;}
    AnmView table{nullptr};if(!host.music_fill_region(temporary,64,table)||!table.data)return false;
    for(u32 i=0;i<8;++i){table.put(i*8,segment*(i+1)-1);table.put(i*8+4,event);}
    if(!host.set_memory_music_notifications(notify,8,temporary,hr))return false;
    if(notify&&!host.release_memory_music_notify(notify,ignored))return false;
    if(!host.free_music_initialize_notify(temporary))return false;if(signed_word(hr)<0){result=0x80004005;return true;}
    u32 object_token=0;if(!host.allocate_music_initialize_object(0xa0,object_token))return false;AnmView object{nullptr};if(!host.music_fill_region(object_token,0xa0,object)||!object.data)return false;
    if(!construct_memory_music_owner(object,0xa0,object_token,buffer,segment*8,stream_token,segment,host,ignored))return false;
    output=object_token;std::memcpy(object.data+0x58,descriptor,36);object.put(0x7c,wrapper_token);object.put(0x98,event);object.put(0x9c,0);result=0;return true;
}
}

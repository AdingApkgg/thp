#include "MusicPlaybackControl.hpp"
namespace th143 {
static double get_double(AnmView v,u32 at){double d;std::memcpy(&d,v.data+at,8);return d;}
static void put_double(AnmView v,u32 at,double d){std::memcpy(v.data+at,&d,8);}
bool music_playback_control(AnmView object,u32 bytes,MusicPlaybackOperation operation,u32 close_file,MusicPlaybackControlHost& host,u32& result){
    if(!object.data||bytes<0xa0)return false;
    const u32 array_token=object.get(4),count=object.get(0x10);AnmView array{nullptr};
    const auto first=[&](u32& token)->bool {if(!host.music_region(array_token,4,array)||!array.data)return false;token=array.get(0);return true;};
    const auto buffers=[&]()->bool {if(count>0x3fffffffu)return false;return !count||(host.music_region(array_token,count*4,array)&&array.data);};
    const auto stream=[&](AnmView& out)->bool {return host.music_region(object.get(12),0xa0,out)&&out.data;};
    const u32 zero=0,uninitialized=0x800401f0;
    if(operation==MusicPlaybackOperation::FirstBuffer){result=0;if(array_token&&count&&!first(result))return false;return true;}
    if(operation==MusicPlaybackOperation::AnyPlaying){
        result=0;if(!array_token)return true;if(!buffers())return false;
        for(u32 i=0;i<count;++i)if(const u32 token=array.get(i*4)){u32 status=0,hr=0;if(!host.music_buffer_status(token,status,hr))return false;result|=status&1;}
        return true;
    }
    if(!array_token){result=uninitialized;return true;}
    if(operation==MusicPlaybackOperation::Stop||operation==MusicPlaybackOperation::Rewind){
        if(!buffers())return false;result=0;
        if(operation==MusicPlaybackOperation::Stop){object.put(0x50,0);object.put(0x54,0);}
        for(u32 i=0;i<count;++i){const u32 token=array.get(i*4);u32 hr=0;
            if(operation==MusicPlaybackOperation::Stop){if(!host.music_buffer_call(token,0x48,nullptr,0,hr))return false;result|=hr;}
            if(!host.music_buffer_call(token,0x34,&zero,1,hr))return false;result|=hr;
        }
        if(operation==MusicPlaybackOperation::Stop){object.put(0x1c,0);if(close_file){AnmView s{nullptr};if(!stream(s))return false;if(s.get(0x78)==1){if(!host.music_file_close(s.get(0x8c)))return false;s.put(0x8c,0xffffffff);}}}
        return true;
    }
    if(operation==MusicPlaybackOperation::Pause){
        if(!object.get(0x50)){object.put(0x54,0);result=uninitialized;return true;}
        object.put(0x50,0);object.put(0x54,1);u32 token=0;if(!first(token)||!host.music_buffer_call(token,0x48,nullptr,0,result))return false;
        double clock;if(!host.music_clock(clock))return false;put_double(object,0x38,clock);
        AnmView s{nullptr},metadata{nullptr};if(!stream(s))return false;u32 position;if(!host.music_file_position(s.get(0x8c),position)||!host.music_region(s.get(0x90),0x34,metadata)||!metadata.data)return false;
        s.put(0x98,position-metadata.get(0x10));
        if(s.get(0x78)==1){if(!host.music_file_close(s.get(0x8c)))return false;s.put(0x8c,0xffffffff);}
        return true;
    }
    if(operation==MusicPlaybackOperation::Resume){
        if(!object.get(0x54)){result=uninitialized;return true;}
        AnmView s{nullptr};if(!stream(s))return false;object.put(0x54,0);
        if(!host.music_stream_reopen(object.get(12),s.get(0x90),s.get(0x98)))return false;
        u32 token=0;if(!first(token))return false;object.put(0x50,1);double clock;if(!host.music_clock(clock))return false;
        clock-=get_double(object,0x38);clock+=get_double(object,0x40);put_double(object,0x40,clock);
        const u32 args[]={0,object.get(0x20),object.get(0x24)};return host.music_buffer_call(token,0x30,args,3,result);
    }
    return false;
}
}

#include "AudioActionMainPump.hpp"
namespace th143 {
bool AudioActionMainPumpHost::music_stream_reopen(u32 token,u32 metadata,u32 position){
    AnmView stream{nullptr},meta{nullptr};if(!music_region(token,0xa0,stream)||!stream.data||!music_region(metadata,0x34,meta)||!meta.data)return false;u32 ignored=0;return reopen_music_file(stream,0xa0,meta,metadata,position,music_file_base(),*this,ignored);
}
static bool action_object(AnmView audio,AudioActionMainPumpHost& host,AnmView& object){const u32 token=audio.get(0x5778);return token&&host.music_region(token,0xa0,object)&&object.data;}
static bool action_first_buffer(AnmView object,AudioActionMainPumpHost& host,u32& buffer){
    auto& playback=static_cast<AudioControlMainPumpHost&>(host);return music_playback_control(object,0xa0,MusicPlaybackOperation::FirstBuffer,0,playback,buffer);
}
static bool action_stop(AnmView object,u32 close,AudioActionMainPumpHost& host){
    auto& playback=static_cast<AudioControlMainPumpHost&>(host);u32 ignored=0;return music_playback_control(object,0xa0,MusicPlaybackOperation::Stop,close,playback,ignored);
}
static bool action_region(AudioActionMainPumpHost& host,u32 token,u32 bytes,AnmView& out){return host.music_region(token,bytes,out)&&out.data;}
static bool copy_action_name(AnmView audio,u32 bytes,u32 source){
    for(u32 i=0;;++i){if(source+i>=bytes||0x23f8+i>=bytes)return false;const u8 value=audio.data[source+i];audio.data[0x23f8+i]=value;if(!value)return true;}
}
bool pump_audio_action_main(AnmView audio,u32 bytes,u8 music,u8 sound,u8 flags,AudioActionMainPumpHost& host,u32& result){
    if(!audio.data||bytes<0x57b0)return false;if(!audio.get(12)){result=0;return true;}
    const u32 first=audio.get(0x24f8);if(first>=5&&first<=9)return pump_audio_track_main(audio,bytes,music,sound,host,result);
    u32 cursor=0x24f8;
    for(u32 passes=0;;++passes){
        if(passes==32||cursor+0x10c>bytes)return false;
        const u32 command=audio.get(cursor);if(command<1||command>9)break;
        // Normal producers reserve the final queue entry as a zero sentinel.
        if(cursor!=0x24f8||command>4)return false;
        const u32 token=audio.get(0x5778),step=audio.get(cursor+8),argument=audio.get(cursor+4);bool compact=false,increment=false,repeat=false;u32 hr=0;AnmView object{nullptr};
        if(command==1){
            if((flags&0x10)&&step){increment=true;}
            else{
                if((flags&0x10)&&!teardown_music(audio,bytes,host))return false;
                const u8* table=nullptr;u32 available=0;if(!host.music_track_table(audio.get(0x1980),table,available))return false;
                if(!preload_music_pcm(audio,bytes,table,available,argument,reinterpret_cast<const char*>(audio.data+cursor+12),bytes-cursor-12,flags,host,hr))return false;
                compact=true;repeat=true;
            }
        }else if(command==2){
            if((flags&0x10)&&signed_word(argument)>=0){
                if(step==0){if(!start_cached_music_slot(audio,bytes,argument,music,flags,host.music_thread_parameter(),host,hr))return false;compact=hr!=0;increment=!compact;}
                else if(step==2){if(!token)increment=true;else{const u32 zero=0;if(!host.music_action_call(0x486af0,token,&zero,1,hr))return false;compact=signed_word(hr)<0;increment=!compact;}}
                else if(step==5){
                    if(!action_object(audio,host,object))return false;u32 buffer=0;if(!action_first_buffer(object,host,buffer))return false;AnmView stream{nullptr},meta{nullptr};if(!action_region(host,object.get(12),0xa0,stream)||!action_region(host,stream.get(0x90),0x34,meta))return false;
                    const u32 loop=u32(meta.get(0x1c)!=0),args[]={buffer,loop,0};audio.put(cursor+4,loop);if(!host.music_action_call(0x485f70,token,args,3,hr))return false;compact=signed_word(hr)<0;increment=!compact;
                }else if(step==7){const u32 args[]={0,1,0};if(!host.music_action_call(0x4863a0,token,args,3,hr))return false;increment=true;}
                else if(signed_word(step)>=20)compact=true;else increment=true;
            }else if(!token)compact=true;
            else{
                if(!action_object(audio,host,object))return false;
                if(step==0){if(!action_stop(object,0,host))return false;increment=true;}
                else if(step==1){
                    if(object.get(0x9c))break;
                    u32 path=cursor+12;if(signed_word(argument)>=0){if(argument>=16)return false;path=0x4678+argument*256;}
                    if(!copy_action_name(audio,bytes,path))return false;const u8* table=nullptr;u32 available=0,track=0;if(!host.music_track_table(audio.get(0x1980),table,available)||!find_music_track(table,available,reinterpret_cast<const char*>(audio.data+path),bytes-path,track))return false;audio.put(cursor+4,track);
                    const u32 metadata=audio.get(0x1980)+track*0x34;if(!host.music_action_call(0x485c90,token,&metadata,1,hr))return false;increment=true;
                }else if(step==2){
                    const u32 metadata=audio.get(0x1980)+argument*0x34,stream_token=object.get(12);AnmView stream{nullptr},meta{nullptr};if(!action_region(host,stream_token,0xa0,stream)||!action_region(host,metadata,0x34,meta))return false;
                    if(!reopen_music_file(stream,0xa0,meta,metadata,0,host.music_file_base(),host,hr))return false;increment=true;
                }else if(step==3){
                    u32 buffer=0;if(!action_first_buffer(object,host,buffer))return false;const u32 zero=0;if(!host.music_action_call(0x486af0,token,&zero,1,hr))return false;
                    // Re-read the owner after the reset helper, just as the caller does.
                    if(!action_object(audio,host,object))return false;AnmView stream{nullptr},meta{nullptr};if(!action_region(host,object.get(12),0xa0,stream)||!action_region(host,stream.get(0x90),0x34,meta))return false;
                    const u32 loop=u32(meta.get(0x1c)!=0),args[]={buffer,loop,0};audio.put(cursor+4,loop);if(!host.music_action_call(0x485f70,audio.get(0x5778),args,3,hr))return false;compact=signed_word(hr)<0;increment=!compact;
                }else if(step==4){const u32 args[]={0,1,0};if(!host.music_action_call(0x4863a0,token,args,3,hr))return false;increment=true;}
                else if(signed_word(step)>=7)compact=true;else increment=true;
            }
        }else if(command==3){
            if(!token)compact=true;else if(step==0){if(!action_object(audio,host,object)||!action_stop(object,1,host))return false;increment=true;}else if(step==1)compact=true;else increment=true;
        }else{
            if(!token)compact=true;
            else if(step==0){if(!action_object(audio,host,object)||!action_stop(object,1,host))return false;increment=true;}
            else if(step==1){if(!audio.get(0x14))compact=true;else{if(!host.post_music_thread_quit(audio.get(0x10)))return false;increment=true;}}
            else if(step==2){
                u32 status=0;if(!host.wait_music_thread(audio.get(0x14),256,status))return false;
                if(status){if(!host.post_music_thread_quit(audio.get(0x10)))return false;audio.put(cursor+8,audio.get(cursor+8)-1);}else audio.put(0x14,0);increment=true;
            }else if(step==3){
                if(!host.close_music_thread(audio.get(0x14))||!host.close_music_thread(audio.get(0x5780)))return false;audio.put(0x14,0);
                if(const u32 current=audio.get(0x5778)){if(!host.delete_music_object(current,1))return false;}audio.put(0x5778,0);increment=true;
            }else if(step==10)compact=true;else increment=true;
        }
        if(increment)audio.put(cursor+8,audio.get(cursor+8)+1);
        if(compact)for(u32 copied=0;copied<31&&audio.get(cursor);++copied){if(cursor+0x218>bytes)return false;std::memcpy(audio.data+cursor,audio.data+cursor+0x10c,0x10c);cursor+=0x10c;}
        if(!repeat)break;
    }
    return dispatch_sound_queue(audio,bytes,sound,0x53b1e0+cursor,host,result);
}
}

#include "AudioTrackMainPump.hpp"
#include "MusicTrackLookup.hpp"
#include "MusicPlaybackPosition.hpp"
namespace th143 {
bool pump_audio_track_main(AnmView audio,u32 bytes,u8 music_enabled,u8 sound_enabled,AudioTrackMainPumpHost& host,u32& result){
    if(!audio.data||bytes<0x57b0)return false;if(!audio.get(12)){result=0;return true;}
    if(audio.get(0x24f8)!=9)return pump_audio_control_main(audio,bytes,music_enabled,sound_enabled,host,result);
    const u32 table_token=audio.get(0x1980);const u8* table=nullptr;u32 table_bytes=0,track=0;
    if(!host.music_track_table(table_token,table,table_bytes)||!find_music_track(table,table_bytes,reinterpret_cast<const char*>(audio.data+0x2504),bytes-0x2504,track))return false;
    const u32 object_token=audio.get(0x5778),metadata_token=table_token+track*0x34;AnmView object{nullptr},stream{nullptr},metadata{nullptr};
    if(!host.music_region(object_token,0xa0,object)||!object.data)return false;double clock=0,position=0;if(!host.music_clock(clock))return false;
    if(!host.music_region(object.get(12),0xa0,stream)||!stream.data||!host.music_region(stream.get(0x90),0x34,metadata)||!metadata.data||!music_playback_position(object,0xa0,metadata,0x34,clock,position))return false;
    if(!host.music_region(object.get(12),0xa0,stream)||!stream.data)return false;stream.put(0x90,metadata_token);
    if(!relocate_music_playback(object,0xa0,object_token,position,host))return false;
    u32 cursor=0x24f8;for(u32 copied=0;copied<31&&audio.get(cursor);++copied){std::memcpy(audio.data+cursor,audio.data+cursor+0x10c,0x10c);cursor+=0x10c;}
    return dispatch_sound_queue(audio,bytes,sound_enabled,0x53b1e0+cursor,host,result);
}
}

#include "MusicNotifyRefillThread.hpp"
namespace th143 {
bool MusicNotifyRefillHost::music_ring_positions(u32 buffer,bool pp,u32& play,bool wp,u32& write,u32& hr){
    const bool first=notify_position_index++==0;if(!notify_position_service(buffer,pp,play,wp,write,hr))return false;
    if(first){if(pp)notify_scratch.first_play=play;if(wp)notify_scratch.first_write=write;}
    else if(pp)notify_scratch.second_play=play;return true;
}
bool MusicNotifyRefillHost::refill_notified_music(u32 token,u32,u32& result){
    AnmView object{nullptr};if(!music_thread_owner(token,object)||!object.data)return false;notify_position_index=0;
    return refill_music_ring(object,0xa0,notify_critical,notify_nesting,notify_scratch,notify_query_output_token,*this,result);
}
bool run_music_notify_refill_thread(AnmView globals,u32 bytes,AnmView message,u32 message_bytes,MusicNotifyRefillHost& host,u32& result){return run_music_notify_thread(globals,bytes,message,message_bytes,host,result);}
}

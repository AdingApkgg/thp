#include "MusicNotifyThread.hpp"
namespace th143 {
bool run_music_notify_thread(AnmView globals,u32 bytes,AnmView message,u32 message_bytes,MusicNotifyThreadHost& host,u32& result){
    if(!globals.data||bytes<12||!message.data||message_bytes<28)return false;bool quitting=false;
    for(u32 waits=0;waits<1000000;++waits){
        u32 outcome=0;if(!host.wait_music_notify(globals.get(8),outcome))return false;
        const u32 token=globals.get(0);if(!token)quitting=true;
        if(outcome==1){
            for(u32 peeks=0;;++peeks){if(peeks==1000000)return false;bool available=false;if(!host.peek_music_notify(message,available))return false;if(!available)break;if(message.get(4)==0x12)quitting=true;}
        }else if(outcome==0&&token){
            AnmView object{nullptr};if(!host.music_thread_owner(token,object)||!object.data)return false;
            if(object.get(0x50)){object.put(0x9c,1);const u32 current=globals.get(0);u32 ignored=0;if(!host.refill_notified_music(current,token,ignored))return false;
                if(!host.music_thread_owner(globals.get(0),object)||!object.data)return false;object.put(0x9c,0);}
        }
        if(quitting){result=0;return true;}
    }
    return false;
}
}

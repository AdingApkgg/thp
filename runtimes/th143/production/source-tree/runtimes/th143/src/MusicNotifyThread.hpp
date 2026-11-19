#pragma once
#include "AnmState.hpp"
namespace th143 {
struct MusicNotifyThreadHost {
    virtual ~MusicNotifyThreadHost()=default;
    virtual bool music_thread_owner(u32 token,AnmView&)=0;
    virtual bool wait_music_notify(u32 event,u32& result)=0;
    virtual bool peek_music_notify(AnmView message,bool& available)=0;
    virtual bool refill_notified_music(u32 object,u32 notification_argument,u32& result)=0;
};
//473700 finite event/message traces. globals[0]=540958 owner,globals[8]=540960
//event (the intervening54095c word is preserved). MSG is the caller's declared
//28byte scratch. The actual worker parameter is unused on this regular path.
bool run_music_notify_thread(AnmView globals,u32 bytes,AnmView message,u32 message_bytes,
                             MusicNotifyThreadHost&,u32& result);
}

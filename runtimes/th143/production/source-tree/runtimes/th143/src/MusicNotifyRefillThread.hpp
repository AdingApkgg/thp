#pragma once
#include "MusicNotifyThread.hpp"
#include "MusicRingRefill.hpp"
namespace th143 {
struct MusicNotifyRefillHost:MusicNotifyThreadHost,MusicRingRefillHost {
    u8 notify_critical=0,notify_nesting=0;
    MusicRingScratch notify_scratch{};
    u32 notify_query_output_token=0;
    virtual bool notify_position_service(u32 buffer,bool play_present,u32& play,bool write_present,u32& write,u32& result)=0;
    bool music_thread_owner(u32 token,AnmView& out)override{return music_fill_region(token,0xa0,out);}
    bool music_ring_positions(u32 buffer,bool pp,u32& play,bool wp,u32& write,u32& hr)final;
    bool refill_notified_music(u32 object,u32 notification_argument,u32& result)final;
private:
    u32 notify_position_index=0;
};
//473700 ->486890 ->486250/485f70/486db0/486eb0. The declared finite API
//model preserves cursor local slots between successive worker invocations;
//external services which overwrite those stack locations require a new ABI
//model. Logical query output address is supplied for the nested call context.
bool run_music_notify_refill_thread(AnmView globals,u32 bytes,AnmView message,u32 message_bytes,
                                    MusicNotifyRefillHost&,u32& result);
}

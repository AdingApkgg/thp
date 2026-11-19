#pragma once
#include "AnmState.hpp"
#include <array>

namespace th143 {
struct SoundQueueHost {
    virtual ~SoundQueueHost()=default;
    virtual bool stop_buffer(u32 token,u32& status)=0;
};
// Original queue storage53b1fc..53d4a4; actual audio device lives in the host.
struct SoundQueue {
    static constexpr u32 bytes=0x22a8;
    std::array<u8,bytes> data{};
    AnmView view(){return {data.data()};}
    bool pause(SoundQueueHost&);
    bool enqueue(u32 sound,i32 priority);
    bool request(u32 sound,bool spatial,float x=0);
private:
    bool enqueue_pan(u32 sound,i32 priority,u32 pan);
};
}

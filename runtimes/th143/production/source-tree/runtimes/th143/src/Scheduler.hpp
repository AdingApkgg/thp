#pragma once
#include "AnmState.hpp"
#include <array>
#include <map>

namespace th143 {
struct SchedulerHost {
    virtual ~SchedulerHost()=default;
    virtual bool invoke(u32 entry,u32 owner,u32& result)=0;
    virtual bool release_callback(u32 token)=0;
};
// Byte-compatible401360/401830 owners; callback code lives in the host.
class Scheduler {
public:
    std::array<u8,0x58> data{};
    std::map<u32,std::array<u8,0x28>> records;
    u32 self=0x6e000000;
    void construct(u8 fill=0);
    bool create(u32 token,u32 entry,u8 fill=0);
    AnmView at(u32 token);
    bool add(u32 token,i32 priority,bool draw,SchedulerHost&,u32& result);
    bool remove(u32 token,SchedulerHost&);
    bool dispatch(bool draw,SchedulerHost&,i32& result,u32 budget=100000);
};
}

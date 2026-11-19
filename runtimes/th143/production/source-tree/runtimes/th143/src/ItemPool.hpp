#pragma once
#include "DirectionVector.hpp"
#include <vector>
#include <array>

namespace th143 {
// Original434df0/419900 storage:600 regular slots and4096 delayed slots.
// Guest links are32-bit semantic addresses, independent of host allocation.
class ItemPool {
public:
    static constexpr u32 count=0x1258,regular_count=600,stride=0xc1c,first=0x14;
    static constexpr u32 bytes=0xde21e8,token_base=0x68000000;
    static constexpr u32 regular_free=0xde21b4,delayed_free=0xde21c4;
    std::vector<u8> data;
    ItemPool():data(bytes,0){}
    u32 get(u32 at) const;
    void put(u32 at,u32 value);
    static u32 token(u32 offset){return token_base+offset;}
    static u32 slot(u32 index){return token(first+index*stride);}
    static u32 offset(u32 address){return address-token_base;}
    void construct();
    void reset_storage();
    // Original436030 types13/14, including empty pool and deferred script
    // binding. Other factories and continuous item motion are separate.
    bool spawn_delayed(i32 type,const std::array<float,3>& position,float angle,float speed,u32 rate_token,u32& result);
    bool release(u32 address);
private:
    void build(u32 sentinel,u32 begin,u32 count);
};
}

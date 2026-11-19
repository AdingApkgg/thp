#pragma once
#include "AnmVm.hpp"
#include <array>
#include <vector>

namespace th143 {
struct AnmPoolGlobals {
    static constexpr u32 base=0x540990;
    std::array<u8,0xf0> transforms{};
};
struct AnmPoolHost {
    virtual ~AnmPoolHost()=default;
    virtual bool register_pool_callback(u32 entry,i32 priority,bool draw,u32 owner)=0;
    virtual bool set_pool_vertex_format(u32)=0;
    virtual bool allocate_pool_fallback(u32& token,AnmView&)=0;
};
// Complete47f3c0 owner storage, including four resource-loader slots and the
// physical8191-slot VM pool. Tokens retain the original manager-relative layout.
class AnmPool {
public:
    static constexpr u32 bytes=0xff75ac,count=8191,first=0xdc,stride=0x5e4,free_node=0xbc7af8;
    std::vector<u8> data;
    u32 self=0x72000000;
    AnmPool():data(bytes){}
    AnmView view(){return {data.data()};}
    AnmView at(u32 token);
    bool construct(AnmPoolGlobals&,AnmPoolHost&);
    bool allocate(u32& token,AnmView&,AnmPoolHost&); //484de0
    bool owns(u32 token)const;
    // 483e67..483eaa. Called after common ANM unlinking, BEFORE buffer release.
    bool return_slot(u32 token,AnmView);
    AnmView find(u32 handle); //484280 pooled branch
};
}

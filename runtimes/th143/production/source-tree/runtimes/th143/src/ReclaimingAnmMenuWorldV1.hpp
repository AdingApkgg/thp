#pragma once
#include "AnmMenuWorld.hpp"
#include <map>
namespace th143 {
// Retire backing bytes only after the consumer has copied the frame's device
// stream. Component audit hosts keep their existing retired-byte snapshots.
class ReclaimingAnmMenuWorldV1:public AnmMenuWorld {
public:
    explicit ReclaimingAnmMenuWorldV1(AnmResourceServices&,u32 heap_base=0x74000000);
    bool allocate_resource_storage(u32,bool,u32&)override;
    bool retire_consumed_storage();
    u32 storage_diagnostic(u32)const;
private:
    AnmResourceServices& runtime_services;
    std::map<u32,u32> owned_ranges,free_ranges;
    u32 release_cursor=0,reclaimed_regions=0,reused_allocations=0,reference_failures=0;
    std::uint64_t reclaimed_bytes=0;
    void return_range(u32,u32);
};
}

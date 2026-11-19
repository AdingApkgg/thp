#pragma once
#include "ResourceCleanup.hpp"

namespace th143 {
struct ResourcePumpMemory:ResourceCleanupMemory {
    // Chunk decoding, texture creation and template generation are supplied by
    // the resource loader. The pump owns selection and retirement ordering.
    virtual bool complete_resource_chunk(u32 resource,u32& result)=0;
};
bool pump_anm_resources(u32 manager,const std::array<u32,2>& heads,ResourcePumpMemory&,i32& result); //4827d0
bool anm_resources_ready(u32 manager,ResourcePumpMemory&,bool& ready); //482860
bool unload_anm_slot(u32 manager,u32 index,const std::array<u32,2>& heads,ResourcePumpMemory&); //4828a0
}

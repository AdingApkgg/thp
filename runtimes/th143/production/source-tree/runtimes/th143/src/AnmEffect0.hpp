#pragma once
#include "AnmResourceWorld.hpp"
namespace th143 {
constexpr u32 anm_effect0_bytes=0x1d04;
//40a1d0/40a310/40a8f0: the screen transition's five embedded ANM VMs.
// Allocation, effect-table installation and40a380 drawing are separate.
bool initialize_anm_effect0(AnmView root,u8* data,u32 self,u32 resource,AnmResourceWorld&);
i32 step_anm_effect0(u8* data,AnmVmHost&);
bool signal_anm_effect0(AnmView root,u8* data,u32 self,u32 resource,i32 signal,AnmResourceWorld&);
}

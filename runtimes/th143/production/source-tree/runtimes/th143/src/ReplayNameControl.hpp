#pragma once
#include "ReplaySaveControl.hpp"
namespace th143 {
struct ReplayNameControlHost:ReplaySaveControlHost {
 virtual bool replay_name_write(const u8* filename,u32 bytes,u32 player_address)=0;
 virtual bool replay_name_load(const u8* filename,u32 bytes,u32& result)=0;
};
// Full4494d0. The91-cell cursor has88 characters, Space, Delete and End;
// 12 editable bytes retain their original spaces/NUL backing. Void x86 return.
bool control_replay_name(AnmView menu,u32 self,u32 return_substate,ReplayNameControlHost&);
}

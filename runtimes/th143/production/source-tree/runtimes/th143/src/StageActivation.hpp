#pragma once
#include "StageInit.hpp"
#include "AnmInstance.hpp"

namespace th143 {
struct StageAnimationMemory {
    virtual ~StageAnimationMemory()=default;
    virtual bool read_stage_animation_memory(u32,void*,u32)=0;
    virtual bool write_stage_animation_memory(u32,const void*,u32)=0;
    virtual AnmView stage_animation_storage(u32 vm)=0;
    virtual AnmView stage_animation_template(u32 resource,i32 script)=0;
};
// 40ee20: activates callbacks, binds every STD primitive and resets script PC.
bool activate_stage(StageState&,StageAnimationMemory&,AnmVmHost&);
bool advance_stage_animations(StageState&,StageAnimationMemory&,AnmVmHost&); //40eef0
}

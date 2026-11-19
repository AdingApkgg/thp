#pragma once
#include "StageScript.hpp"

namespace th143 {
struct StageFrameServices {
    virtual ~StageFrameServices()=default;
    virtual bool set_stage_animation_rate(float value,float& previous)=0;
    virtual bool update_stage_warp(StageState&)=0;
};
// Original40d630. Stage geometry submission remains in the draw callbacks;
// this update normalizes the view direction and publishes the camera globals.
i32 advance_stage_frame(StageState&,u32 self,StageScriptGlobals&,StageAnimationMemory&,AnmVmHost&,StageFrameServices&);
}

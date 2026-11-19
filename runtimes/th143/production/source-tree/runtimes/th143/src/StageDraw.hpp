#pragma once
#include "StageActivation.hpp"
#include "StageProjection.hpp"
namespace th143 {
struct StageDrawGlobals {
    u32 camera_token=0,camera_kind=0,depth_write=0,depth_test=0;
    i32 origin_x=0,origin_y=0;
};
struct StageDrawServices:StageCameraServices {
    virtual bool set_stage_render_state(u32 state,u32 value)=0;
    virtual bool set_stage_viewport(const u8* viewport)=0;
    virtual bool set_stage_sprite_mode(u8 enabled)=0;
    virtual bool submit_stage_animation(u32 token,AnmView)=0;
};
// 410390 and40ef90: inline animations, camera/device state, STD instance
// culling, primitive placement/scaling and ordered animation submissions.
// Actual ANM vertex generation/rasterization belongs to the submit service.
bool draw_stage_layer(StageState&,u32 self,i32 layer,StageCamera&,StageDrawGlobals&,StageAnimationMemory&,StageDrawServices&,u32 budget=1000000);
}

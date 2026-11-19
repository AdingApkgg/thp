#pragma once
#include "StageDraw.hpp"
#include "ApplicationFrame.hpp"
namespace th143 {
struct StagePresentationServices:StageDrawServices {
    virtual bool set_stage_tint(bool enabled,u32 color)=0;
    virtual bool clear_stage_viewport(const ApplicationClear&)=0;
    virtual bool draw_background_layer(i32 layer)=0;
    virtual bool draw_animation_layer(u32 layer)=0;
};
// Normal 40df80 /40e440 draw callbacks, before/after ordinary ANM layers.
// Fade/countdown transitions have an explicit unsupported return.
bool present_stage_background(StageState&,StageCamera&,StageDrawGlobals&,StagePresentationServices&,bool foreground);
}

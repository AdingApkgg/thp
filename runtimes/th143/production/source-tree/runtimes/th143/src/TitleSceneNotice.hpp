#pragma once
#include "AnmState.hpp"
namespace th143 {
struct TitleSceneNoticeHost:AnmTimerHost {
 virtual bool title_notice_create(u32 id)=0;
 virtual bool title_notice_destroy()=0;
 virtual bool title_notice_dialog(AnmView title)=0;
 virtual bool title_notice_responses()=0;
};
//4624e0 phase2 notice branch plus the outer45f6e0 timer. Regular input remains
// in TitleScenePage; an existing owner or pending queue consumes this frame.
bool advance_title_scene_notice(AnmView title,AnmView save,AnmView notice,u32 owner,TitleSceneNoticeHost&,bool& handled,u32& result);
}

#pragma once
#include "TitleMainIntro.hpp"
#include "MenuCursor.hpp"
namespace th143 {
struct TitleMainKeys {u32 fresh=0,repeated=0;bool started_before=false;};
struct TitleMainHost {virtual ~TitleMainHost()=default;virtual bool title_sound(u32 id)=0;};
//45fb70 main selection and exit-delay substates2/4, including45f6e0's
// timer tail. State3's game startup and state5's first-start path are separate.
bool advance_title_main_control(GameTitleRuntime&,AnmResourceWorld&,const TitleMainKeys&,TitleMainHost&,u32& result);
}

#pragma once
#include "TitleOptionControl.hpp"
#include "TrophyTextLookup.hpp"
namespace th143 {
struct TitleNicknameEntryBindings {AnmView title,catalog,save,scratch;u32 self;};
//Full465890 phases0/2 through45f6e0 outerclock. Phase1 navigation, notices and
//the hidden rawkeyboard sequence are separate. Native critical-section flag0.
bool advance_title_nickname_entry(TitleNicknameEntryBindings,TitleOptionControlHost&,u32& result);
}

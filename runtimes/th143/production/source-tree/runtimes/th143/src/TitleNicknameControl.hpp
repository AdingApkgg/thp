#pragma once
#include "TitleNicknameEntry.hpp"
#include "TrophyGridNavigation.hpp"
namespace th143 {
//Full465890 phase1 via45f6e0. Generic memory/call services include the raw
//402af0 keyboard capture, Notice ownership and lower ANM/text/music operations.
bool advance_title_nickname_control(TitleNicknameEntryBindings,TitleOptionControlHost&,u32& result);
}

#pragma once
#include "MusicNotifyThread.hpp"
namespace th143 {
struct MusicNotifyDispatchState {bool quitting=false,finished=false;u32 result=0;};
//One complete 473700 wait outcome and message drain, with lifetime state kept
//between host scheduler turns. No synthetic WM_QUIT is inserted at a yield.
bool dispatch_music_notification(AnmView globals,u32 bytes,AnmView message,u32 message_bytes,
                                 MusicNotifyDispatchState&,MusicNotifyThreadHost&);
}

#pragma once
#include "AudioActionMainPump.hpp"
namespace th143 {
//472640 for the normal cached filename domain: source lies inside the actual
//audio allocation and has a terminator within its256byte path slot. Native
//lookup uses a128byte stack basename buffer: at most127 basename bytes.
bool queue_music_cached_path(AnmView audio,u32 bytes,u32 path,
                              AudioActionMainPumpHost&,u32& result);
}

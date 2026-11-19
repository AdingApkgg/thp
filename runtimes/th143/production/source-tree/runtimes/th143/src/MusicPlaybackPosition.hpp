#pragma once
#include "AnmState.hpp"
namespace th143 {
//486ff0 arithmetic after its declared clock46f4e0 service. Positive finite
// format/cycle domain; loop subtraction order is preserved, never replaced by fmod.
bool music_playback_position(AnmView object,u32 object_bytes,AnmView metadata,
                             u32 metadata_bytes,double clock,double& position);
}

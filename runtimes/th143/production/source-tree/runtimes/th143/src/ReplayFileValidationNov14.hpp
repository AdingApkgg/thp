#pragma once
#include "AnmState.hpp"
namespace th143 {
enum class ReplayFileValidation:u32 {Valid=0,BadHeader=1,Truncated=2,BadSize=3,BadPayload=4};
// Read-only untrusted-file boundary. Original valid-file decode stays unchanged.
ReplayFileValidation validate_replay_file(const u8*,u32);
}

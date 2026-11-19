#pragma once
#include "AnmState.hpp"
namespace th143 {
enum class ReplaySemanticValidation:u32 {Valid=0,BadHeader=1,Truncated=2,BadSize=3,BadPayload=4,BadMetadata=5,BadInput=6};
ReplaySemanticValidation validate_replay_semantic_file(const u8*,u32);
ReplaySemanticValidation validate_replay_decoded_payload(const u8*,u32);
}

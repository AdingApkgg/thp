#pragma once
#include "AnmState.hpp"
#include <vector>
namespace th143 {
struct EarnedAchievementRecovery {
 bool eligible=false;
 u32 uniqueScenes=0;
 std::vector<u32> requests;
};
// Read-only plan for legacy port saves that missed the original award service.
// Applying the requests belongs to the original-controlled achievement host.
EarnedAchievementRecovery plan_earned_achievement_recovery(AnmView);
}

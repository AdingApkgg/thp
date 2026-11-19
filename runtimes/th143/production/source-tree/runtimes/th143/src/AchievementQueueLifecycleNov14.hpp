#pragma once
#include "AchievementUnlockNov14.hpp"
namespace th143 {
void change_achievement_phase(AnmView,u32);
bool construct_achievement_queue(AnmView,u32,AchievementUnlockHost&);
bool start_achievement_queue(AnmView,u32,u32,AchievementUnlockHost&,u32&);
// Single-thread original mode; removes callbacks and retires both resource lists.
bool destroy_achievement_queue(AnmView,AchievementUnlockHost&);
}

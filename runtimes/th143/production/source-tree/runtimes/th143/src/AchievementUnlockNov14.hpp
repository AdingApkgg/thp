#pragma once
#include "AnmState.hpp"
namespace th143 {
struct AchievementUnlockHost {
 virtual ~AchievementUnlockHost()=default;
 virtual bool achievement_read(u32,void*,u32)=0;
 virtual bool achievement_write(u32,const void*,u32)=0;
 virtual bool achievement_call(u32,u32,const u32*,u32,u32&)=0;
};
// 467e00: persistent flag, duplicate suppression, existing queue or new queue.
bool unlock_achievement(AnmView save,u32 id,AchievementUnlockHost&,u32& result);
}

#pragma once
#include "AchievementQueueLifecycleNov14.hpp"
namespace th143 {
struct AchievementQueueUpdateHost {
 virtual ~AchievementQueueUpdateHost()=default;
 virtual bool achievement_spawn(u32 resource,u32 script,u32& handle)=0;
 virtual bool achievement_find(u32 handle,u32& vm)=0;
 virtual bool achievement_name(u32 id,u32& text)=0;
 virtual bool achievement_text(u32 vm,u32 format,u32 text,bool substitution)=0;
 virtual bool achievement_sound(u32)=0;
 virtual bool achievement_rate(u32,float&)=0;
 virtual bool achievement_destroy(u32)=0;
};
// 467ed0. ANM creation/lookup/text, audio and owned destruction are services.
bool update_achievement_queue(AnmView,u32,AchievementQueueUpdateHost&,u32&);
}

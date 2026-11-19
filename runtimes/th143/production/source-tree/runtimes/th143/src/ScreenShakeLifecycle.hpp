#pragma once
#include "ScreenShake.hpp"
namespace th143 {
struct ScreenShakeLifecycleHost {
 virtual ~ScreenShakeLifecycleHost()=default;
 virtual bool shake_allocate(u32 bytes,u32& token,AnmView&)=0;
 virtual bool shake_callback(u32 entry,u32& token,AnmView&)=0;
 virtual bool shake_register(u32 token,i32 priority)=0;
 virtual bool shake_remove(u32 token)=0;
 virtual bool shake_release(u32 token)=0;
};
bool create_screen_shake(i32 duration,i32 start,i32 end,ScreenShakeLifecycleHost&,u32& self,AnmView&);
bool destroy_screen_shake(AnmView,u32 self,bool release_self,ScreenShakeLifecycleHost&);
}

#include "ScreenShakeLifecycle.hpp"
namespace th143 {
bool create_screen_shake(i32 duration,i32 start,i32 end,ScreenShakeLifecycleHost& host,u32& self,AnmView& s){
 if(!host.shake_allocate(0x44,self,s))return false;if(!self)return true;if(!s.data)return false;
 std::memset(s.data,0,0x44);s.put(0,2);
 u32 callback;AnmView record;if(!host.shake_callback(0x471650,callback,record)||!record.data)return false;
 record.put(0x24,self);record.put(4,record.get(4)|2u);
 if(!host.shake_register(callback,20))return false;s.put(8,callback);record.put(0x10,0x471a30);
 s.put(0x40,s.get(0x40)|1);s.put(0x3c,0x4e40b0);s.put(0x30,0xffffffff);s.put(0x34,0);s.put(0x38,0);
 s.put(0x1c,u32(duration));s.put(0x20,u32(start));s.put(0x24,u32(end));s.put(0x10,1);s.put(0x28,0);return true;
}
bool destroy_screen_shake(AnmView s,u32 self,bool release_self,ScreenShakeLifecycleHost& host){
 if(!s.data)return !self;
 if(s.get(8)&&!host.shake_remove(s.get(8)))return false;
 if(s.get(12)&&!host.shake_remove(s.get(12)))return false;
 return !release_self||host.shake_release(self);
}
}

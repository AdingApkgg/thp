#include "NoticeLifecycle.hpp"
#include <initializer_list>
namespace th143 {
bool construct_notice(AnmView state,u32 self,NoticeLifecycleHost& host){
 u32 token;AnmView callback;
 if(!host.notice_callback(0x4472d0,token,callback)||!callback.data)return false;
 callback.put(4,callback.get(4)&~2u);callback.put(0x24,self);
 if(!host.notice_register(token,11,false))return false;state.put(8,token);
 if(!host.notice_callback(0x4472e0,token,callback)||!callback.data)return false;
 callback.put(4,(callback.get(4)&~2u)|1u);callback.put(12,0);callback.put(16,0);callback.put(0x24,self);
 if(!host.notice_register(token,69,true))return false;state.put(12,token);
 if(!host.notice_start_worker(0x446b00))return false;
 u32 flags=state.get(0x24);if(!(flags&1)){flags|=1;state.put(0x18,0);state.put(0x14,0xfff0bdc1);state.put(0x1c,0);state.put(0x20,0x4e40b0);state.put(0x24,flags);}
 state.put(0x18,0);state.put(0x1c,0);state.put(0x14,0xffffffff);state.put(0x10,0);return true;
}
bool destroy_notice(AnmView state,NoticeLifecycleGlobals& g,NoticeLifecycleHost& host){
 if(state.get(8)&&!host.notice_remove_callback(state.get(8)))return false;
 if(state.get(12)&&!host.notice_remove_callback(state.get(12)))return false;
 for(auto* slot:{&g.notice_resource,&g.congratulations_resource})if(*slot){if(!host.notice_destroy_resource(*slot)||!host.notice_release(*slot))return false;*slot=0;}
 g.owner=0;return true;
}
bool create_notice(u32 id,NoticeLifecycleGlobals& g,NoticeLifecycleHost& host,u32& self,AnmView& state){
 if(!host.notice_allocate(0x1b8,self,state)||!self||!state.data)return false;
 std::memset(state.data,0,0x1b8);g.owner=self;state.put(0,state.get(0)|2);
 if(!construct_notice(state,self,host))return false;state.put(0x120,id);return true;
}
bool delete_notice(AnmView state,u32 self,NoticeLifecycleGlobals& g,NoticeLifecycleHost& host){return destroy_notice(state,g,host)&&host.notice_release(self);}
}

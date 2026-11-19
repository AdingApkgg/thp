#pragma once
#include "AnmState.hpp"
namespace th143 {
struct NoticeLifecycleGlobals {u32 owner=0,notice_resource=0,congratulations_resource=0;};
struct NoticeLifecycleHost {
 virtual ~NoticeLifecycleHost()=default;
 virtual bool notice_allocate(u32 bytes,u32& token,AnmView& state)=0;
 virtual bool notice_callback(u32 entry,u32& token,AnmView& state)=0;
 virtual bool notice_register(u32 token,i32 priority,bool draw)=0;
 virtual bool notice_start_worker(u32 entry)=0;
 virtual bool notice_remove_callback(u32 token)=0;
 virtual bool notice_destroy_resource(u32 token)=0;
 virtual bool notice_release(u32 token)=0;
};
//446c00/446d00/446e20/446ec0; asynchronous worker execution is separate.
bool construct_notice(AnmView,u32 self,NoticeLifecycleHost&);
bool destroy_notice(AnmView,NoticeLifecycleGlobals&,NoticeLifecycleHost&);
bool create_notice(u32 id,NoticeLifecycleGlobals&,NoticeLifecycleHost&,u32& self,AnmView&);
bool delete_notice(AnmView,u32 self,NoticeLifecycleGlobals&,NoticeLifecycleHost&);
}

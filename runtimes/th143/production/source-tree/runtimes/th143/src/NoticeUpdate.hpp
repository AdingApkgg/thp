#pragma once
#include "MenuCursor.hpp"
namespace th143 {
struct NoticeUpdateHost:AnmTimerHost {
 virtual bool notice_read_word(u32 address,u32& value)=0;
 virtual bool notice_texture_reset(u32 info)=0;
 virtual bool notice_texture_upload(u32 info,u32 data,u32 bytes,u32 mode)=0;
 virtual bool notice_free_file(u32 data)=0;
 virtual bool notice_texture_release(u32 texture)=0;
 virtual bool notice_animation(u32 resource,i32 script,u32& handle)=0;
 virtual bool notice_signal(u32 handle,i32 signal)=0;
 virtual bool notice_sound(u32 id)=0;
 virtual bool notice_worker(u32 entry)=0;
 virtual bool notice_format(char* target,u32 capacity,i32 id)=0;
 virtual bool notice_resource_increment(u32 resource)=0;
 virtual bool notice_allocate_vm(u32& token,AnmView&)=0;
 virtual bool notice_initialize_vm(u32 resource,u32 vm,i32 script)=0;
 virtual bool notice_update_vm(u32 vm)=0;
 virtual bool notice_register_vm(u32 vm,u32& handle)=0;
};
//446f00 /4472d0. Full notification state machine; declared graphics/file/audio services.
bool update_notice(AnmView,u32 fresh,NoticeUpdateHost&);
inline u32 draw_notice(){return 1;} //4472e0
}

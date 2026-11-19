#pragma once
#include "AnmState.hpp"
namespace th143 {
struct PreviewReadbackParameters {u32 screen_width=640,screen_height=480,width=288,height=336,source_surface=0;};
struct PreviewReadbackHost {
 virtual ~PreviewReadbackHost()=default;
 virtual bool create_preview_surface(u32 width,u32 height,u32 format,u32 pool,u32& surface,i32& status)=0;
 virtual bool copy_preview_surface(u32 source,u32 destination,i32& status)=0;
 virtual bool lock_preview_surface(u32 surface,const u8*& pixels,u32& accessible_bytes,u32& pitch,i32& status)=0;
 virtual bool unlock_preview_surface(u32 surface)=0;
 virtual bool release_preview_surface(u32 surface)=0;
};
//4115f0: GPU service responses are explicit; row copy/alpha writes are CPU code.
bool readback_clear_preview(u8* pixels,u32 bytes,const PreviewReadbackParameters&,PreviewReadbackHost&,i32& result);
}

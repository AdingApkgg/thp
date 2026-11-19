#pragma once
#include "AnmVm.hpp"
#include <string>

namespace th143 {
struct AnmTextureRequest {
    enum Kind {embedded,blank,render_target,external} kind;
    u32 entry=0,source=0,source_bytes=0,width=0,height=0,format=0;
    i32 x=0,y=0;
};
struct ResourceLoaderHost:AnmVmHost {
    virtual bool allocate_resource_storage(u32 bytes,bool array,u32& token)=0;
    virtual bool release_resource_storage(u32 token)=0;
    virtual bool read_resource_file(const std::string&,bool external,u32& token,u32& size)=0;
    virtual bool create_resource_texture(const AnmTextureRequest&,i32& status,u32& width,u32& height)=0;
    virtual bool build_resource_template(u32 vm,u32 resource,u32 script)=0;
    virtual u32 resource_viewport_width()const=0;
    virtual u32 resource_viewport_height()const=0;
};
// Original4820a0/481f00/4821e0, followed by482140's pending marker.
// Cached requests return immediately; the caller owns the worker wait.
bool request_anm_resource(u32 manager,u32 index,const std::string&,ResourceLoaderHost&,u32& resource);
// Original4822e0/4824d0/482a90: one chunk, then templates on the last chunk.
// Texture transfer is a host service. Sprite descriptor word17 is unused
// uninitialized x86 stack padding and is deliberately not materialized.
bool complete_anm_resource_chunk(u32 resource,ResourceLoaderHost&,u32& result);
}

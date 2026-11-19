#pragma once
#include "AnmBatch.hpp"
namespace th143 {
struct AnmStaticMeshDevice {
    virtual ~AnmStaticMeshDevice()=default;
    virtual bool create_static_mesh(u32 bytes,u32 usage,u32 format,u32 pool,u32& token)=0;
    virtual bool lock_static_mesh(u32 buffer,u32 offset,u32 bytes,u32 flags,u32& data)=0;
    virtual bool unlock_static_mesh(u32 buffer)=0;
    virtual bool bind_static_mesh(u32 stream,u32 buffer,u32 offset,u32 stride,i32& status)=0;
};
// 4808c0: allnine256x256 anchor quads,720-byte XYZ/UV vertexbuffer and the
// separate96-byte global scratch (each24-byte vertex preserves word3).
bool initialize_anm_static_mesh(u32 manager,std::array<u8,96>& scratch,AnmRenderMemory&,AnmStaticMeshDevice&,i32& status);
}

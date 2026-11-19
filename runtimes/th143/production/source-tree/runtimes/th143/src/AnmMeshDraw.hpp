#pragma once
#include "AnmRenderState.hpp"
#include "AnmTransform.hpp"
#include "Matrix4.hpp"
namespace th143 {
struct AnmMeshDevice {
    virtual ~AnmMeshDevice()=default;
    virtual bool mesh_transform(u32 kind,const Matrix4&)=0;
    virtual bool mesh_stream(u32 stream,u32 buffer,u32 offset,u32 stride)=0;
    virtual bool mesh_primitive(u32 type,u32 first,u32 count)=0;
};
// 47c6d0: cached ordered Euler world matrix, texture matrix, tint factor and
// fixed20-byte XYZ/UV mesh stream. The actual vertex buffer is a device input.
i32 draw_anm_mesh(u32 manager,u32 current_manager,AnmView,const AnmViewport&,u32& depth_test,AnmRenderMemory&,AnmSpriteDevice&,AnmMeshDevice&,AnmTransformHost&);
}

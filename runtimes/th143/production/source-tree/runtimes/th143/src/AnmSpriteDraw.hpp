#pragma once
#include "AnmQuadSubmit.hpp"
#include "AnmRotatedQuad.hpp"
namespace th143 {
struct AnmMeshDevice;
struct AnmPrimitiveDevice;
struct AnmSpriteDrawHost:AnmTransformHost {
    virtual bool draw_callback(u32 entry,AnmView)=0;
    virtual AnmMeshDevice* mesh_device(){return nullptr;}
    virtual AnmPrimitiveDevice* primitive_device(){return nullptr;}
    virtual u32 physical_width()const{return 640;}
    virtual u32 physical_height()const{return 480;}
};
// 47db40. Modes0..4/6/8,16/20/21/22 and24/25 generate quads, billboards,
// fixed meshes, untextured rectangles or VM-owned triangle strips;
// native no-op cases are preserved. Other geometry modes return -2.
i32 draw_anm_sprite(u32 manager,u32 current_manager,AnmView vm,AnmView camera,AnmQuad& scratch,const AnmViewport&,u32& depth_test,AnmRenderMemory&,AnmSpriteDevice&,AnmSpriteDrawHost&,u32 rounding=0);
}

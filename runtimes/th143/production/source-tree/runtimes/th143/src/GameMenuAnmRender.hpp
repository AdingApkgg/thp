#pragma once
#include "AnmMenuWorld.hpp"
#include "GameAnmEffect0Draw.hpp"
namespace th143 {
// Uses the existing renderer's cameras, quad, batches and device. Only the
// three overlay layers that can contain effect0 need an additional callback.
class GameMenuAnmRender final:private AnmRenderMemory,private AnmSpriteDrawHost {
public:
    GameMenuAnmRender(GameRenderRuntime& render,GameRenderDevice& device,AnmMenuWorld& world,u32& width,u32& height):render(render),device(device),world(world),width(width),height(height){}
    bool draw_pool_callback(u32 entry);
private:
    GameRenderRuntime& render;GameRenderDevice& device;AnmMenuWorld& world;u32& width;u32& height;
    bool read_render_memory(u32,void*,u32)override;
    bool write_render_memory(u32,const void*,u32)override;
    AnmView transform_parent(u32 p)override{return world.state(p);}
    bool draw_callback(u32,AnmView)override;
};
}

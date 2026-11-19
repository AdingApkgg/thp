#pragma once
#include "GameOwnerRuntime.hpp"
#include "GameStageRuntime.hpp"
#include "AnmResourceWorld.hpp"
#include "ApplicationFrame.hpp"
#include "AnmSpriteDraw.hpp"
#include "PlayerDraw.hpp"
#include "StagePresentation.hpp"
#include "AnmStaticMesh.hpp"
#include "AnmMeshDraw.hpp"
#include "AnmPrimitive.hpp"
#include "AnmStripDraw.hpp"
#include "ApplicationCameras.hpp"
#include "AsciiDraw.hpp"
namespace th143 {
struct GameRenderDevice:AnmSpriteDevice,ApplicationFrameDevice,AnmMeshDevice,AnmPrimitiveDevice,AnmStaticMeshDevice {
    virtual u32 game_device_token()const=0;
    virtual bool read_game_render_memory(u32,void*,u32){return false;}
    virtual bool write_game_render_memory(u32,const void*,u32){return false;}
    bool mesh_transform(u32 kind,const Matrix4& m)override{return application_transform(game_device_token(),kind,reinterpret_cast<const u8*>(m.data()));}
    bool mesh_stream(u32,u32,u32,u32)override{return false;}
    bool mesh_primitive(u32,u32,u32)override{return false;}
    bool primitive_upload(u32,u32,u32,const u8*,u32)override{return false;}
    bool create_static_mesh(u32,u32,u32,u32,u32&)override{return false;}
    bool lock_static_mesh(u32,u32,u32,u32,u32&)override{return false;}
    bool unlock_static_mesh(u32)override{return false;}
    bool bind_static_mesh(u32,u32,u32,u32,i32&)override{return false;}
};
// A renderer over the existing gameplay owners and ANM world. It allocates no
// replacement Stage/Player/pool or private resource world. The device owns GPU
// calls; frame setup, positions, quad generation, state caches and batching
// execute here. Unbound owner draw bodies fail at the caller's dispatch bridge.
class GameRenderRuntime final:public PlayerDrawHost,public AsciiDrawHost,private AnmRenderMemory,private AnmSpriteDrawHost,private StagePresentationServices,private StageAnimationMemory {
public:
    GameRenderRuntime(GameOwnerRuntime& o,GameStageRuntime& s,AnmResourceWorld& w,GameRenderDevice& d):owners(o),stage(s),world(w),device(d){}
    std::array<u8,0xa34> application{};
    AnmQuad quad;
    ApplicationFrameGlobals frame;
    //53b0f8/fc is the gameplay clip origin. It is distinct from the two
    // ANM transform origins at53b108/10c and53b110/114.
    std::array<i32,2> playfield_origin{128,16};
    StageCamera render_camera;
    StageDrawGlobals drawing;
    std::array<u8,96> static_scratch{};
    u32 depth_test=0,submitted=0,error=0;
    bool initialize(const u8* cameras,u32 bytes,const AnmPoolGlobals&,bool static_mesh=false);
    bool begin_frame();
    bool draw_player_visual(u32 token,AnmView)override;
    bool flush();
    bool present_stage(bool foreground);
    //4831a0..4836b0: all38 registered pool draw wrappers, including their
    // camera/depth transitions. The caller retains the shared Scheduler order.
    bool draw_pool_callback(u32 entry);
    bool draw_ascii_glyph(AnmView)override;
    bool present_ascii(u32 entry,AnmView owner);
private:
    static constexpr u32 app_self=0x4e47d0,manager=0x72000000;
    GameOwnerRuntime& owners;GameStageRuntime& stage;AnmResourceWorld& world;GameRenderDevice& device;
    bool read_render_memory(u32,void*,u32)override;
    bool write_render_memory(u32,const void*,u32)override;
    AnmView transform_parent(u32)override;
    bool draw_callback(u32 entry,AnmView)override;
    AnmMeshDevice* mesh_device()override{return &device;}
    AnmPrimitiveDevice* primitive_device()override{return &device;}
    u32 physical_width()const override{return frame.width;}
    u32 physical_height()const override{return frame.height;}
    AnmView storage(u32,u32 bytes=AnmView::bytes);
    void publish_drawing();
    bool select_camera(u32 offset,u32 kind);
    bool draw_pool_layer(u32 layer);
    bool set_depth_state(u32 kind,u32 value);
    i32 render_animation(AnmView vm,AnmView camera);
    bool read_stage_animation_memory(u32 p,void* out,u32 n)override{return read_render_memory(p,out,n);}
    bool write_stage_animation_memory(u32 p,const void* in,u32 n)override{return write_render_memory(p,in,n);}
    AnmView stage_animation_storage(u32 p)override{return storage(p);}
    AnmView stage_animation_template(u32 p,i32 script)override{auto* r=world.resource(p);return r&&script>=0&&u32(script)<r->templates.size()?AnmView{r->templates[u32(script)].data()}:AnmView{nullptr};}
    bool has_animation_manager()const override{return bool(world.pool);}
    bool flush_stage_camera_batch()override{return flush();}
    bool set_stage_camera_transform(u32 kind,const u8* bytes)override{return device.application_transform(device.game_device_token(),kind,bytes);}
    bool set_stage_camera_origin(u32 x,u32 y)override{return world.write(manager+0xd0,&x,4)&&world.write(manager+0xd4,&y,4);}
    bool set_stage_render_state(u32 kind,u32 value)override{return device.render_state(kind,value);}
    bool set_stage_viewport(const u8* bytes)override{return device.application_viewport(device.game_device_token(),bytes);}
    bool set_stage_sprite_mode(u8 value)override{return world.write(manager+0xbc81a0,&value,1);}
    bool set_stage_tint(bool enabled,u32 color)override{const u32 v=enabled;return world.write(manager+0xff75a8,&v,4)&&world.write(manager+0xff75a4,&color,4);}
    bool clear_stage_viewport(const ApplicationClear& value)override{return device.clear_application(device.game_device_token(),value);}
    bool draw_background_layer(i32)override;
    bool draw_animation_layer(u32)override;
    bool submit_stage_animation(u32,AnmView)override;
};
}

#pragma once
#include "ApplicationTargets.hpp"
#include "AnmResourceWorld.hpp"
#include "AnmTextureStore.hpp"
#include "GameOwnerRuntime.hpp"
namespace th143 {
struct GameApplicationTargetDevice {
    virtual ~GameApplicationTargetDevice()=default;
    virtual bool application_backbuffer(u32 device,u32& surface)=0;
    virtual bool release_application_backbuffer(u32 surface)=0;
};
// The four application-owned VMs (443957..4439d8) use the game allocator.
// Target script selection/rebuild is shared with the original446460 port;
// texture surfaces retain the persistent resource store's actual ownership.
class GameApplicationTargets final:public AnmRenderMemory,public ApplicationTargetServices {
public:
    GameApplicationTargets(AnmView app,AnmResourceWorld& world,AnmTextureStore& textures,GameOwnerServices& storage,GameApplicationTargetDevice& device):app(app),world(world),textures(textures),storage(storage),device(device){}
    bool construct();
    bool initialize(ApplicationTargetGlobals& g){return initialize_application_targets(app,g,*this,*this);}
    bool release(ApplicationTargetGlobals& g){return release_application_targets(app,g,*this,*this);}
    bool read_render_memory(u32,void*,u32)override;
    bool write_render_memory(u32,const void*,u32)override;
    AnmView target_animation(u32)override;
    bool copy_target_template(u32,i32,u32)override;
    bool advance_target_animation(u32)override;
    bool target_backbuffer(u32,u32&)override;
    bool target_surface(u32,u32&)override;
    bool release_target_surface(u32)override;
private:
    struct Vm {u32 token=0;std::array<u8,AnmView::bytes> data;};
    std::array<Vm,4> vms;
    u8* mapped(u32,u32);
    AnmView app;
    AnmResourceWorld& world;
    AnmTextureStore& textures;
    GameOwnerServices& storage;
    GameApplicationTargetDevice& device;
};
}

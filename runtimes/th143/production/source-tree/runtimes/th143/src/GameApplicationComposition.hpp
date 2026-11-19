#pragma once
#include "ApplicationComposition.hpp"
#include "GameApplicationTargets.hpp"
#include "GameRenderRuntime.hpp"
namespace th143 {
struct GameApplicationCompositionCallbacks {
    virtual ~GameApplicationCompositionCallbacks()=default;
    virtual bool application_composition_callback(u32)=0;
};
// Application composition and gameplay use the same renderer, application,
// ANM pool and device. The four offscreen-target VMs are ordinary real draws.
class GameApplicationComposition final:private AnmRenderMemory,private ApplicationCompositionServices {
public:
    GameApplicationComposition(GameRenderRuntime& render,GameApplicationTargets& targets,AnmResourceWorld& world,GameRenderDevice& device,GameApplicationCompositionCallbacks& callbacks):render(render),targets(targets),world(world),device(device),callbacks(callbacks){}
    bool reset_batches();
    bool begin_frame(ApplicationFrameGlobals&,bool reset=true);
    bool draw(ApplicationCompositionPass,ApplicationCompositionGlobals&);
private:
    bool read_render_memory(u32,void*,u32)override;
    bool write_render_memory(u32,const void*,u32)override;
    bool composition_render_state(u32,u32,u32)override;
    bool draw_composition_animation(u32,u32)override;
    bool draw_composition_layer(u32,u32)override;
    bool invoke_composition_callback(u32 p)override{return callbacks.application_composition_callback(p);}
    void synchronize_render_state();
    GameRenderRuntime& render;GameApplicationTargets& targets;AnmResourceWorld& world;GameRenderDevice& device;GameApplicationCompositionCallbacks& callbacks;
};
}

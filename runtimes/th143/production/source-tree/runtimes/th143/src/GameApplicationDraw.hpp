#pragma once
#include "GameApplicationComposition.hpp"
namespace th143 {
struct GameApplicationDrawServices {
    virtual ~GameApplicationDrawServices()=default;
    virtual bool application_owner_draw(u32 entry,u32 owner,u32& result)=0;
};
//443daa..443ee4: ten application draw registrations and initial backbuffer.
// Full4438a0/update-state construction is owned by the application startup.
class GameApplicationDraw final:private SchedulerHost {
public:
    GameApplicationDraw(Scheduler& scheduler,GameOwnerServices& storage,GameApplicationComposition& composition,GameApplicationTargets& targets,GameRenderRuntime& render,AnmResourceWorld& world,GameApplicationDrawServices& services):scheduler(scheduler),storage(storage),composition(composition),targets(targets),render(render),world(world),services(services){}
    ApplicationFrameGlobals frame;
    ApplicationCompositionGlobals globals;
    u32 independent_signals=0,menu_owner=0,failed_entry=0;
    std::vector<u32> trace;
    bool register_callbacks();
    bool dispatch(i32& result);
private:
    bool registered=false;
    bool invoke(u32,u32,u32&)override;
    bool release_callback(u32)override{return false;}
    Scheduler& scheduler;GameOwnerServices& storage;GameApplicationComposition& composition;GameApplicationTargets& targets;GameRenderRuntime& render;AnmResourceWorld& world;GameApplicationDrawServices& services;
};
}

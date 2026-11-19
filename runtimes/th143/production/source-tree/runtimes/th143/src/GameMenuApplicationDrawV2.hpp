#pragma once
#include "GameApplicationDraw.hpp"
#include "GameMenuAnmRender.hpp"
#include "ApplicationDrawPrelude.hpp"
namespace th143 {
// Extends the registered application dispatch with the menu transition draw.
// Registrations and public frame/trace state remain owned by the application.
class GameMenuApplicationDrawV2 final:private SchedulerHost {
public:
    GameMenuApplicationDrawV2(GameApplicationDraw& base,Scheduler& scheduler,GameApplicationComposition& composition,GameRenderRuntime& render,GameRenderDevice& device,AnmMenuWorld& world,GameApplicationDrawServices& services):base(base),scheduler(scheduler),composition(composition),render(render),device(device),world(world),services(services),menu(render,device,world,world.width,world.height){}
    bool dispatch(i32& result);
private:
    GameApplicationDraw& base;Scheduler& scheduler;GameApplicationComposition& composition;GameRenderRuntime& render;GameRenderDevice& device;AnmMenuWorld& world;GameApplicationDrawServices& services;GameMenuAnmRender menu;
    bool invoke(u32,u32,u32&)override;
    bool release_callback(u32)override{return false;}
};
}

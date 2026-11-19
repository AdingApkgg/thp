#pragma once
#include "GameMenuApplicationDraw.hpp"
#include "GameApplicationFinalDraw.hpp"
namespace th143 {
// The same registered application dispatcher, extended for a live gameplay
// menu owner at its final pass. No private registrations or renderer are made.
class GameGameplayApplicationDraw final:private SchedulerHost {
public:
    GameGameplayApplicationDraw(GameApplicationDraw& b,Scheduler& s,GameApplicationComposition& c,GameRenderRuntime& r,GameRenderDevice& d,AnmMenuWorld& w,GameApplicationDrawServices& io,AnmView m):base(b),scheduler(s),composition(c),render(r),device(d),world(w),services(io),menu(m),animations(r,d,w,w.width,w.height){}
    bool dispatch(i32& result);
private:
    GameApplicationDraw& base;Scheduler& scheduler;GameApplicationComposition& composition;GameRenderRuntime& render;GameRenderDevice& device;AnmMenuWorld& world;GameApplicationDrawServices& services;AnmView menu;GameMenuAnmRender animations;
    bool invoke(u32,u32,u32&)override;
    bool release_callback(u32)override{return false;}
};
}

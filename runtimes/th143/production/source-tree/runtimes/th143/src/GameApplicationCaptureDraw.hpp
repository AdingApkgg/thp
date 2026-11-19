#pragma once
#include "GameGameplayApplicationDraw.hpp"
#include "GameAuxRuntime.hpp"
namespace th143 {
//446290 with both4116e0 screenshot passes and4481d0 menu composition.
bool finish_capture_application_draw(GameRenderRuntime&,GameRenderDevice&,GameAuxRuntime&,AnmView menu);
class GameCaptureApplicationDraw final:private SchedulerHost {
public:
    GameCaptureApplicationDraw(GameApplicationDraw& b,Scheduler& s,GameApplicationComposition& c,GameRenderRuntime& r,GameRenderDevice& d,AnmMenuWorld& w,GameApplicationDrawServices& io,GameAuxRuntime& a,AnmView m):base(b),scheduler(s),composition(c),render(r),device(d),world(w),services(io),auxiliary(a),menu(m),animations(r,d,w,w.width,w.height){}
    bool dispatch(i32& result);
private:
    GameApplicationDraw& base;Scheduler& scheduler;GameApplicationComposition& composition;GameRenderRuntime& render;GameRenderDevice& device;AnmMenuWorld& world;GameApplicationDrawServices& services;GameAuxRuntime& auxiliary;AnmView menu;GameMenuAnmRender animations;
    bool invoke(u32,u32,u32&)override;
    bool release_callback(u32)override{return false;}
};
}

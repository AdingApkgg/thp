#pragma once
#include "GameCommonRuntime.hpp"
#include "CommonLoadingDraw.hpp"
namespace th143 {
struct CommonFrameBindings {
    GameCommonRuntime* common=nullptr;GameAsciiRuntime* ascii=nullptr;AnmResourceWorld* world=nullptr;
    AnmView application{nullptr};ApplicationTargetGlobals* targets=nullptr;CommonApplicationGlobals* globals=nullptr;
    AnmRenderMemory* memory=nullptr;ApplicationTargetServices* graphics=nullptr;
};
// Place outside the gameplay/draw service adapter, before cold factories.
// Both common callback entries share the actual GameFrameRuntime/Scheduler;
// all other registered owners retain their existing update/render services.
class GameCommonFrameServices final:public GameFrameServices {
public:
    explicit GameCommonFrameServices(GameFrameServices& next):next(next){}
    CommonFrameBindings bindings;
    bool frame_input(GameInputFrame& g)override{return next.frame_input(g);}
    bool before_game_callback(u32 e,u32 o)override{return next.before_game_callback(e,o);}
    bool after_game_callback(u32 e,u32 o,u32 r)override{return next.after_game_callback(e,o,r);}
    bool other_game_callback(u32,u32,u32&)override;
    bool release_game_callback(u32 p)override{return next.release_game_callback(p);}
private:GameFrameServices& next;
};
}

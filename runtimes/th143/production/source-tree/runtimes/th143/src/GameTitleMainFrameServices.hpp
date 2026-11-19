#pragma once
#include "GameTitleFrameServices.hpp"
#include "TitleMainControl.hpp"
namespace th143 {
// Adds the main-page input/exit-delay bodies to the existing title adapter.
// Key repeat is supplied by the application's input owner.
class GameTitleMainFrameServices final:public GameFrameServices {
public:
    GameTitleMainFrameServices(GameFrameServices& next,TitleMainHost& host):next(next),host(host){}
    GameTitleRuntime* title=nullptr;AnmResourceWorld* world=nullptr;TitleMainKeys keys;
    bool frame_input(GameInputFrame& g)override{return next.frame_input(g);}
    bool before_game_callback(u32 e,u32 o)override{return next.before_game_callback(e,o);}
    bool after_game_callback(u32 e,u32 o,u32 r)override{return next.after_game_callback(e,o,r);}
    bool release_game_callback(u32 p)override{return next.release_game_callback(p);}
    bool other_game_callback(u32 e,u32 o,u32& result)override{
        if(title&&world&&o==GameTitleRuntime::self&&title->global_owner==o&&e==0x45fb20&&title->view().get(0x1c)==1){const u32 phase=title->view().get(0x24);if(phase==2||phase==4)return advance_title_main_control(*title,*world,keys,host,result);}
        return next.other_game_callback(e,o,result);
    }
private:GameFrameServices& next;TitleMainHost& host;
};
}

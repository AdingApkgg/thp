#pragma once
#include "TitleMainIntro.hpp"
namespace th143 {
// A narrow title-page adapter over the application's existing frame services.
// Other title pages/music/activation reject until their real bodies are bound.
class GameTitleFrameServices final:public GameFrameServices {
public:
    explicit GameTitleFrameServices(GameFrameServices& next):next(next){}
    GameTitleRuntime* title=nullptr;AnmResourceWorld* world=nullptr;
    bool frame_input(GameInputFrame& g)override{return next.frame_input(g);}
    bool before_game_callback(u32 e,u32 o)override{return next.before_game_callback(e,o);}
    bool after_game_callback(u32 e,u32 o,u32 r)override{return next.after_game_callback(e,o,r);}
    bool release_game_callback(u32 p)override{return next.release_game_callback(p);}
    bool other_game_callback(u32 e,u32 o,u32& result)override{if(o!=GameTitleRuntime::self)return next.other_game_callback(e,o,result);if(!title||!world||title->global_owner!=o)return false;if(e==0x45fb20)return !(title->view().get(0xe000)&1)&&advance_title_main_intro(*title,*world,result);if(e==0x45fb30&&title->view().get(0x1c)==1){result=1;return true;}return false;}
private:GameFrameServices& next;
};
}

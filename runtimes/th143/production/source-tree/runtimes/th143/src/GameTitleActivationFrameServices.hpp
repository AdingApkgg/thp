#pragma once
#include "GameTitleFrameServices.hpp"
#include "TitleActivation.hpp"
namespace th143 {
class GameTitleActivationFrameServices final:public GameFrameServices {
public:
    explicit GameTitleActivationFrameServices(GameFrameServices& next):next(next){}
    TitleActivationBindings* bindings=nullptr;CheatControllerGlobals cheat_globals;
    CheatControllerHost* cheat_update=nullptr;CheatDrawHost* cheat_draw=nullptr;
    bool frame_input(GameInputFrame& g)override{return next.frame_input(g);}
    bool before_game_callback(u32 e,u32 o)override{return next.before_game_callback(e,o);}
    bool after_game_callback(u32 e,u32 o,u32 r)override{return next.after_game_callback(e,o,r);}
    bool release_game_callback(u32 p)override{return next.release_game_callback(p);}
    bool other_game_callback(u32 e,u32 o,u32& result)override{
        if(bindings){auto& b=*bindings;if(o==GameTitleRuntime::self&&e==0x45fb20)return advance_title_activation(b,result);if(o==GameCheatRuntime::self){result=1;if(e==0x438330)return cheat_update&&b.cheat.update(cheat_globals,*cheat_update);if(e==0x438340)return cheat_draw&&b.cheat.draw(b.save.view(),b.ascii.view(),*cheat_draw);}}
        return next.other_game_callback(e,o,result);
    }
private:GameFrameServices& next;
};
}

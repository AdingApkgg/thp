#pragma once
#include "TitleScenePage.hpp"
#include "TitleSceneDraw.hpp"
#include "GameTitleCheatServices.hpp"
namespace th143 {
class GameTitleSceneFrameServices final:public GameFrameServices {
public:
    explicit GameTitleSceneFrameServices(GameFrameServices& next):next(next){}
    TitleSceneEntryBindings* entry=nullptr;TitleScenePageBindings* page=nullptr;TitleMainKeys keys;GameTitleCheatServices* cheat=nullptr;CheatControllerGlobals cheat_globals;
    bool frame_input(GameInputFrame& g)override{return next.frame_input(g);}
    bool before_game_callback(u32 e,u32 o)override{return next.before_game_callback(e,o);}
    bool after_game_callback(u32 e,u32 o,u32 r)override{return next.after_game_callback(e,o,r);}
    bool release_game_callback(u32 p)override{return next.release_game_callback(p);}
    bool other_game_callback(u32 e,u32 o,u32& result)override{
        if(page&&cheat&&o==GameCheatRuntime::self){auto& owners=page->owners;result=1;if(e==0x438340)return owners.cheat.draw(owners.save.view(),owners.ascii.view(),*cheat);if(e==0x438330){cheat_globals.fresh=keys.fresh;cheat_globals.repeated=keys.repeated;cheat_globals.primary=page->equipment[0];cheat_globals.secondary=page->equipment[1];cheat_globals.saved_primary=page->saved_equipment[0];cheat_globals.saved_secondary=page->saved_equipment[1];cheat_globals.menu_token=GameTitleRuntime::self;cheat_globals.menu_animation=owners.title.view().get(0x514);cheat_globals.unlock=owners.save.data[0xefac];if(!owners.cheat.update(cheat_globals,*cheat))return false;page->equipment[0]=cheat_globals.primary;page->equipment[1]=cheat_globals.secondary;page->saved_equipment[0]=cheat_globals.saved_primary;page->saved_equipment[1]=cheat_globals.saved_secondary;return true;}}
        if(page&&o==GameTitleRuntime::self&&page->owners.title.global_owner==o&&page->owners.title.view().get(0x1c)==11){
            if(e==0x45fb20){const u32 phase=page->owners.title.view().get(0x24);if(!phase&&entry)return enter_title_scene_page(*entry,result);if(phase==1||phase==2)return advance_title_scene_page(*page,keys,result);}
            if(e==0x45fb30){result=1;return draw_title_scene_page(page->owners.title,page->owners.ascii,page->owners.save,page->owners.world);}
        }
        return next.other_game_callback(e,o,result);
    }
private:GameFrameServices& next;
};
}

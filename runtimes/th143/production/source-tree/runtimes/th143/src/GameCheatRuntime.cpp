#include "GameCheatRuntime.hpp"
namespace th143 {
bool GameCheatRuntime::cheat_owner_storage(u32& token,AnmView& out){
    if(global_owner||!services.reserve_game_owner(self,u32(data.size())))return false;
    data.fill(services.game_allocation_fill());token=self;out=view();return true;
}
bool GameCheatRuntime::create(u32& result){result=0;return !global_owner&&create_cheat_owner(global_owner,result,frames.scheduler,animations,*this);}
bool GameCheatRuntime::destroy(){return destroy_current_cheat_owner(global_owner,frames.scheduler,animations,*this);}
bool GameCheatRuntime::begin_scene(i32 mode,const CheatSceneGlobals& globals){return global_owner&&begin_cheat_scene(view(),mode,globals,animations,overlay);}
bool GameCheatRuntime::position(){return global_owner&&position_cheat_scene(view(),animations);}
bool GameCheatRuntime::return_scene(){return global_owner&&return_cheat_scene(view());}
bool GameCheatRuntime::end_scene(){return global_owner&&end_cheat_scene(view(),animations);}
bool GameCheatRuntime::update(CheatControllerGlobals& globals,CheatControllerHost& host){return global_owner&&update_cheat_controller(view(),globals,animations,overlay,host);}
bool GameCheatRuntime::draw(AnmView save,AnmView ascii,CheatDrawHost& host){return global_owner&&draw_cheat_owner(view(),save,ascii,animations,host);}
}

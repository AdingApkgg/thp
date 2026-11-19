#include "GameMenuRuntime.hpp"
namespace th143 {
bool GameMenuRuntime::bind(AnmView vm,u32 self,i32 script){
    AnmWorld::Resource* r=nullptr;for(auto& candidate:animations.resources)if(candidate.file==0){r=&candidate;break;}
    if(!r||script<0||u32(script)>=r->templates.size())return false;anm_copy_template(vm,self,{r->templates[u32(script)].data()},animations.global_rate_token());vm.put(0x594,0);return anm_step(vm,animations)!=-2;
}
bool GameMenuRuntime::create(u32 width,u32& result){
    result=0;if(global_owner||!services.reserve_game_owner(self,PauseMenu::bytes))return false;
    menu.construct();global_owner=self;auto m=menu.view();
    for(auto row:{std::array<u32,4>{0x448170,10,0,8},{0x448180,71,1,12}}){
        u32 token;if(!services.allocate_game_storage(0x28,token)||!token)return false;const u32 fill=u32(services.game_allocation_fill())*0x01010101u;
        if(!frames.register_callback(token,row[0],self,i32(row[1]),row[2]!=0,(fill&~3u)|1))return false;m.put(row[3],token);
    }
    //4477d0 publishes both initialized timers before its file-read boundary.
    for(u32 at:{0x10,0x24}){if(!(m.get(at+16)&1)){m.put(at+12,animations.global_rate_token());m.put(at+16,m.get(at+16)|1);}m.put(at,0xffffffff);m.put(at+4,0);m.put(at+8,0);}
    std::vector<u8> raw;if(!files.read_game_menu_file("hint.txt",raw)||!services.allocate_game_storage(u32(raw.size()),hint_token)||!hint_token)return false;
    if(!menu.initialize(raw.data(),u32(raw.size()),hint_token,m.get(8),m.get(12),width,*this,animations.global_rate_token()))return false;
    result=self;return true;
}
bool GameMenuRuntime::activate(){if(!global_owner)return false;for(u32 at:{8,12}){auto cb=frames.scheduler.at(menu.view().get(at));if(!cb.data)return false;cb.put(4,cb.get(4)|2);}return true;}
bool GameMenuRuntime::destroy(){
    if(!global_owner)return true;auto m=menu.view();for(u32 at:{8,12})if(m.get(at)&&!frames.scheduler.remove(m.get(at),*this))return false;
    for(u32 i=0;i<25;++i){const u32 recording=m.get(0x204+i*4);if(recording&&(!files.destroy_game_menu_recording(recording)||!services.release_game_storage(recording)))return false;}
    if(m.get(0xfa0)){if(!files.release_game_menu_storage(m.get(0xfa0),true))return false;m.put(0xfa0,0);}
    const u32 second=m.get(0xf84);global_owner=0;if(second&&!files.release_game_menu_storage(second,true))return false;m.put(0xf84,0);
    const u32 first=m.get(0x9b8);if(first&&!files.release_game_menu_storage(first,true))return false;m.put(0x9b8,0);
    return services.release_game_storage(self);
}
i32 GameMenuRuntime::update(SaveData& save,GameOverGlobals& globals,PauseMenuInput& input,AnmView hud,PauseControlHost& host){return global_owner?pause_menu_frame(menu,save,globals,input,animations,overlay,hud,host):-2;}
bool GameMenuRuntime::failure(SaveData& save,GameOverGlobals& globals,u32 reason,GameOverHost& host){return global_owner&&game_over(menu,save,globals,animations,overlay,reason,host);}
}

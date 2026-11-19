#include "GameHudRuntime.hpp"
namespace th143 {
bool GameHudRuntime::hud_owner_storage(u32& token,AnmView& out){if(globals.owner||!services.reserve_game_owner(self,u32(data.size())))return false;data.fill(services.game_allocation_fill());token=self;out=view();return true;}
bool GameHudRuntime::load_hud_scene_animation(u32 name,u32& token){if(!files.load_hud_scene_animation(name,token))return false;globals.scene_resource=token;return true;}
bool GameHudRuntime::hud_callback_read(u32 token,u32& flags){auto cb=frames.scheduler.at(token);if(!cb.data||!frames.scheduler.records.count(token))return false;flags=cb.get(4);return true;}
bool GameHudRuntime::hud_callback_write(u32 token,u32 flags){auto cb=frames.scheduler.at(token);if(!cb.data||!frames.scheduler.records.count(token))return false;cb.put(4,flags);return true;}
bool GameHudRuntime::hud_ascii_resource(u32& token){for(auto& r:animations.resources)if(r.file==2){token=r.token;return true;}return false;}
bool GameHudRuntime::create(u32& result){result=0;return !globals.owner&&create_hud_owner(globals,result,frames.scheduler,animations,*this);}
bool GameHudRuntime::load_scene(i32& result){return globals.owner&&load_hud_scene(view(),globals.scene,static_cast<HudOwnerHost&>(*this),result);}
bool GameHudRuntime::reset_scene(){return globals.owner&&reset_hud_scene(view(),globals,frames.scheduler,animations,*this);}
bool GameHudRuntime::begin_scene(){return globals.owner&&begin_hud_scene(view(),*this);}
bool GameHudRuntime::initialize(HudInitializeGlobals& g){return globals.owner&&initialize_hud(view(),g,animations,*this);}
bool GameHudRuntime::update(HudFrameHost& host){return globals.owner&&update_hud(view(),animations,host);}
bool GameHudRuntime::message(AnmView save,HudMessageGlobals& g,HudMessageHost& host){return globals.owner&&update_hud_message(view(),save,g,host);}
bool GameHudRuntime::destroy(){return destroy_current_hud_owner(globals,frames.scheduler,animations,*this);}
}

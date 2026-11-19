#pragma once
#include "GameOwnerRuntime.hpp"
#include "CheatFactory.hpp"
#include "CheatController.hpp"
#include "CheatDraw.hpp"
namespace th143 {
// Cheat owner lifecycle shares the same resource world, allocator and Scheduler
// as the other Root factories. FrameServices routes438330/438340 here.
class GameCheatRuntime final:private CheatFactoryHost {
public:
    static constexpr u32 self=0x6b004000;
    GameCheatRuntime(GameFrameRuntime& f,AnmWorld& a,AnmOverlay& o,GameOwnerServices& s)
        :frames(f),animations(a),overlay(o),services(s){}
    std::array<u8,0x498> data{};
    u32 global_owner=0;
    AnmView view(){return {data.data()};}
    bool create(u32& result);
    bool destroy();
    bool begin_scene(i32 mode,const CheatSceneGlobals&);
    bool position();
    bool return_scene();
    bool end_scene();
    bool update(CheatControllerGlobals&,CheatControllerHost&);
    bool draw(AnmView save,AnmView ascii,CheatDrawHost&);
private:
    GameFrameRuntime& frames;AnmWorld& animations;AnmOverlay& overlay;GameOwnerServices& services;
    bool cheat_resource(u32 slot,const char* name,u32& token)override{return services.request_game_resource(slot,name,token);}
    bool cheat_callback_storage(u32& token,u8& fill)override{fill=services.game_allocation_fill();return services.allocate_game_storage(0x28,token)&&token;}
    bool cheat_resource_error()override{return false;}
    bool cheat_owner_storage(u32& token,AnmView& out)override;
    bool cheat_owner_view(u32 token,AnmView& out)override{if(token!=self)return false;out=view();return true;}
    bool cheat_owner_release(u32 token)override{return token==self&&services.release_game_storage(token);}
    bool invoke(u32,u32,u32&)override{return false;}
    bool release_callback(u32 token)override{return services.release_game_storage(token);}
};
}

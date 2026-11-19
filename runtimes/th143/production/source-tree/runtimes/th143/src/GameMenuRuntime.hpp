#pragma once
#include "GameOwnerRuntime.hpp"
#include "PauseMenuControl.hpp"
namespace th143 {
struct GameMenuServices {
    virtual ~GameMenuServices()=default;
    virtual bool read_game_menu_file(const char* name,std::vector<u8>&)=0;
    virtual bool release_game_menu_storage(u32 token,bool array)=0;
    virtual bool destroy_game_menu_recording(u32 token)=0;
};
//447d20 factory,447be0 cleanup and448170 updates belong to the same session
// Scheduler/ANM world as Root's other owners. Submenus retain typed services.
class GameMenuRuntime final:private PauseMenuHost,private SchedulerHost {
public:
    static constexpr u32 self=0x6b020000;
    GameMenuRuntime(GameFrameRuntime& f,AnmWorld& a,AnmOverlay& o,GameOwnerServices& s,GameMenuServices& io)
        :frames(f),animations(a),overlay(o),services(s),files(io){menu.self=self;}
    PauseMenu menu;
    u32 global_owner=0,hint_token=0;
    bool create(u32 width,u32& result);
    bool activate();
    bool destroy();
    i32 update(SaveData&,GameOverGlobals&,PauseMenuInput&,AnmView hud,PauseControlHost&);
    bool failure(SaveData&,GameOverGlobals&,u32 reason,GameOverHost&);
private:
    GameFrameRuntime& frames;AnmWorld& animations;AnmOverlay& overlay;GameOwnerServices& services;GameMenuServices& files;
    bool bind(AnmView,u32 self,i32 script)override;
    bool invoke(u32,u32,u32&)override{return false;}
    bool release_callback(u32 p)override{return services.release_game_storage(p);}
};
}

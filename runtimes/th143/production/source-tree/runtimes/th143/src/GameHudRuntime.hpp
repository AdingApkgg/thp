#pragma once
#include "GameOwnerRuntime.hpp"
#include "HudOwner.hpp"
#include "HudInitialize.hpp"
#include "HudScene.hpp"
#include "HudFrame.hpp"
#include "HudMessage.hpp"
namespace th143 {
struct GameHudServices:HudLoadHost {
    virtual bool game_hud_message_storage(u32 token,AnmView&)=0;
    virtual bool release_game_hud_storage(u32 token,bool array)=0;
    virtual bool release_game_hud_resource(u32 token)=0;
};
// Persistent HUD owner for Root loading/startup and callbacks12/33. File,
// descriptor and message-VM ownership belongs to the shared session services.
class GameHudRuntime final:private HudOwnerHost,private HudInitializeHost,private HudSceneHost {
public:
    static constexpr u32 self=0x6b006000;
    GameHudRuntime(GameFrameRuntime& f,AnmWorld& a,GameOwnerServices& s,GameHudServices& io)
        :frames(f),animations(a),services(s),files(io){}
    std::array<u8,0x2b8> data{};
    HudOwnerGlobals globals;
    AnmView view(){return {data.data()};}
    bool create(u32&);
    bool load_scene(i32& result);
    bool reset_scene();
    bool begin_scene();
    bool initialize(HudInitializeGlobals&);
    bool update(HudFrameHost&);
    bool message(AnmView save,HudMessageGlobals&,HudMessageHost&);
    bool destroy();
private:
    GameFrameRuntime& frames;AnmWorld& animations;GameOwnerServices& services;GameHudServices& files;
    bool hud_load_read(u32 p,void* out,u32 n)override{return files.hud_load_read(p,out,n);}
    bool hud_load_write(u32 p,const void* in,u32 n)override{return files.hud_load_write(p,in,n);}
    bool load_hud_scene_animation(u32,u32&)override;
    bool read_hud_message_file(u32 name,u32& token)override{return files.read_hud_message_file(name,token);}
    bool hud_load_error()override{return files.hud_load_error();}
    bool hud_cached_file_log(u32 name)override{return files.hud_cached_file_log(name);}
    bool hud_front_resource(u32& token)override{return services.request_game_resource(5,"front.anm",token);}
    bool hud_callback_storage(u32& token,u8& fill)override{fill=services.game_allocation_fill();return services.allocate_game_storage(0x28,token)&&token;}
    bool hud_owner_storage(u32&,AnmView&)override;
    bool hud_owner_view(u32 token,AnmView& out)override{if(token!=self)return false;out=view();return true;}
    bool hud_message_view(u32 token,AnmView& out)override{return files.game_hud_message_storage(token,out);}
    bool hud_release_storage(u32 token,bool array)override{return token==self&&!array?services.release_game_storage(token):files.release_game_hud_storage(token,array);}
    bool hud_release_scene_resource(u32 token)override{return files.release_game_hud_resource(token);}
    bool invoke(u32,u32,u32&)override{return false;}
    bool release_callback(u32 token)override{return services.release_game_storage(token);}
    bool hud_callback_read(u32 token,u32& flags)override;
    bool hud_callback_write(u32 token,u32 flags)override;
    bool hud_ascii_resource(u32& token)override;
    bool hud_scene_signal(u32 handle,i32 signal)override{return signal_animation(animations,handle,signal);}
};
}

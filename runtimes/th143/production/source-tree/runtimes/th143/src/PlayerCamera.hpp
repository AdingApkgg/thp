#pragma once
#include "PlayerBomb.hpp"
namespace th143 {
struct PlayerCameraGlobals : PlayerBombGlobals {
    u32 held=0,released=0,screen_width=640;
    float viewport_scale=1;
};
struct PlayerCameraHost : PlayerBombHost {
    virtual bool camera_enemy(bool& manager_present,bool& actor_present,std::array<float,3>&)=0;
    virtual bool camera_rate(float)=0;
    virtual bool camera_surface(u32& token,AnmView& vm,std::array<float,2>& texture_size)=0;
    virtual bool camera_surface_view(u32 token,AnmView& vm,std::array<float,2>& texture_size)=0;
    virtual bool camera_request_capture()=0;
    virtual bool camera_photo(i32 script,u32& handle)=0;
    virtual bool camera_bullets(AnmView position,const std::array<float,3>& size,float angle)=0; //417650,kind0
    virtual bool camera_lasers(AnmView position,const std::array<float,3>& size,float angle)=0; //4392d0
};
//458520 primary1; the4582e0 admission visuals are PlayerEquipmentVisual.
bool update_player_camera(AnmView,AnmView equipment,PlayerState*,AnmView cheat,PlayerCameraGlobals&,AnmWorld&,PlayerCameraHost&);
}

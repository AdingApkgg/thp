#include "GamePlayerCameraAim.hpp"
namespace th143 {
namespace {
struct AimHost:PlayerCameraHost {
    GameOwnerRuntime& owners;GameEnemyRuntime& manager;EnemyScripts& scripts;AnmResourceWorld& world;
    AimHost(GameOwnerRuntime& o,GameEnemyRuntime& m,EnemyScripts& s,AnmResourceWorld& w):owners(o),manager(m),scripts(s),world(w){}
    bool timer_rate(u32 p,float& rate)override{return world.timer_rate(p,rate);}
    u32 global_rate_token()const override{return world.global_rate_token();}
    bool camera_enemy(bool& present,bool& actor,std::array<float,3>& position)override{present=manager.global_owner!=0;actor=false;position={0,0,0};if(!present)return true;const u32 token=manager.view().get(0x5c);if(!token)return true;for(const auto& a:scripts.storage)if(a->token==token){actor=true;for(u32 i=0;i<3;++i)position[i]=a->state.fields.floating(0x44+i*4);return true;}return false;}
    bool bomb_option_busy(u32 p,bool& busy)override{u32 value;if(!owners.read(p+0x1c,&value,4))return false;busy=value!=0;return true;}
    bool bomb_alternate_release()override{return false;}
    bool bomb_sound(u32,float)override{return false;}
    bool bomb_stop_sound(u32)override{return false;}
    bool bomb_bullets(AnmView,float)override{return false;}
    bool bomb_lasers(AnmView,float)override{return false;}
    bool camera_rate(float)override{return false;}
    bool camera_surface(u32&,AnmView&,std::array<float,2>&)override{return false;}
    bool camera_surface_view(u32,AnmView&,std::array<float,2>&)override{return false;}
    bool camera_request_capture()override{return false;}
    bool camera_photo(i32,u32&)override{return false;}
    bool camera_bullets(AnmView,const std::array<float,3>&,float)override{return false;}
    bool camera_lasers(AnmView,const std::array<float,3>&,float)override{return false;}
};
}
bool update_game_player_camera_aim(AnmView option,GameOwnerRuntime& owners,GameEnemyRuntime& manager,EnemyScripts& scripts,AnmView cheat,PlayerCameraGlobals& globals,AnmResourceWorld& world){AimHost host{owners,manager,scripts,world};return update_player_camera(option,owners.equipment.view(),&owners.player,cheat,globals,world,host);}
}

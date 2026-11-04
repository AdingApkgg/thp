// Read-only expanded camera observation; independent from clock experiments.
#include "th14-rng-perspective-clock-experiment-fixture-nov04.cpp"
namespace {SceneCamera full_camera_sample;u32 full_camera_callback=0;bool full_camera_installed=false;}
API(full_camera_install) u32 full_camera_install(){
 if(full_camera_installed||public_player_observations!=1||!session.battle)return 0;
 full_camera_installed=true;static auto previous=session.battle->before_player_update;
 session.battle->before_player_update=[](const GameBattle& battle){
  previous(battle);full_camera_sample=session.compositor.world_camera;full_camera_callback=public_player_observations;
 };
 return 1;
}
API(full_camera_word) u32 full_camera_word(u32 index){
 if(index>=75||index==22||index==23)return ~0u;
 u32 offset=index<18?index*4:index<21?offsetof(SceneCamera,target_offset)+(index-18)*4:index==21?offsetof(SceneCamera,fov):offsetof(SceneCamera,view)+(index-24)*4;
 u32 value;std::memcpy(&value,reinterpret_cast<const u8*>(&full_camera_sample)+offset,4);return value;
}
API(full_camera_observed_callback) u32 full_camera_observed_callback(){return full_camera_callback;}

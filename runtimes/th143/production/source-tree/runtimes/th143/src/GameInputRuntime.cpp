#include "GameInputRuntime.hpp"
namespace th143 {
bool GameInputRuntime::initialize_recording(GameManagerInitGlobals& g){return initialize_game_manager_recording(manager,self,g,services);}
bool GameInputRuntime::begin_scene(PlayerState& player,GameManagerSceneGlobals& g){
    g.keyboard=input.keyboard;const bool okay=begin_game_manager_scene(manager,self,player,g,services);input.keyboard=g.keyboard;return okay;
}
bool GameInputRuntime::frame(const GameInputFrame& g){
    input.root_present=g.root_present;input.root_flags=g.root_flags;input.dialog=g.dialog;input.raw_keys=g.raw_keys;input.focus_flags=g.focus_flags;input.stage_value=g.stage_value;
    return record_game_manager_frame(manager,self,input,services);
}
i32 GameInputRuntime::replay_control(bool present,u32 flags,u32 keys){return game_manager_replay_control(manager,present,flags,keys);}
}

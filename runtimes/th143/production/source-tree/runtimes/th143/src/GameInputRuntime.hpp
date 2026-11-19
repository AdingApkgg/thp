#pragma once
#include "GameManagerRecord.hpp"
namespace th143 {
struct GameInputServices:GameManagerInitHost,GameManagerSceneHost {};
struct GameInputFrame {
    bool root_present=false;
    u32 root_flags=0,dialog=0,raw_keys=0,focus_flags=0;
    float stage_value=0;
};
// Persistent input/recording owner for the application's16/35 callbacks.
// The application supplies its live initial globals and owns the allocator,
// callback registration, raw device keys, Root and Stage state.
class GameInputRuntime {
public:
    GameInputRuntime(u32 self,GameInputServices& services):self(self),services(services){manager.construct();}
    bool initialize_recording(GameManagerInitGlobals&);
    bool begin_scene(PlayerState&,GameManagerSceneGlobals&);
    bool frame(const GameInputFrame&);
    // Root and device state are reread by callback35, after other callbacks.
    i32 replay_control(bool root_present,u32 root_flags,u32 raw_keys);
    u32 held()const{return key_word(0x184);}
    u32 fresh()const{return key_word(0x190);}
    u32 released()const{return key_word(0x194);}
    u32 self;
    GameManagerState manager;
    GameManagerRecordGlobals input;
private:
    GameInputServices& services;
    u32 key_word(u32 at)const{u32 value;std::memcpy(&value,input.keyboard.data()+at,4);return value;}
};
}

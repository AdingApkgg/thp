#pragma once
#include "SaveData.hpp"
namespace th143 {
struct SceneCompletionGlobals {
 u32 flags=0,day=0,within_day=0,scene=0,score=0,primary=0,alternate=0,signals=0;
 u32 root_mode=0,equipment_used=0;bool audio_active=false;
 std::array<u32,10> day_first{},day_count{};
};
struct SceneCompletionHost:SaveDataHost {
 virtual bool clear_bonus(u32& score)=0;
 virtual bool finish_player_shots()=0;
 virtual bool stop_completion_audio()=0;
 virtual bool capture_clear_preview(u32 day,u32 within_day)=0;
 virtual bool open_completion_message(i32)=0;
 virtual bool open_results_menu()=0;
 virtual bool finish_replay()=0;
};
//433940; Save item-level calculations execute through the real SaveData body.
bool complete_scene(SaveData&,SceneCompletionGlobals&,SceneCompletionHost&);
}

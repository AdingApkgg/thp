// Observe Player-boundary replay cursors alongside the full camera.
#include "th14-render-dimensions-observer-fixture-nov04.cpp"
namespace {u32 replay_cursor_sample[4]{},replay_cursor_sample_callback=0;bool replay_cursor_installed=false;}
API(replay_cursor_install) u32 replay_cursor_install(){
 if(replay_cursor_installed||public_player_observations!=1||!session.battle)return 0;
 replay_cursor_installed=true;static auto previous=session.battle->before_player_update;
 session.battle->before_player_update=[](const GameBattle& battle){
  previous(battle);
  const auto& replay=session.playback;const auto* stage=replay.stage(replay.selected_stage());
  replay_cursor_sample[0]=replay.selected_stage();replay_cursor_sample[1]=replay.frame();
  replay_cursor_sample[2]=replay.callback_frame();replay_cursor_sample[3]=stage?stage->frames:0;
  replay_cursor_sample_callback=public_player_observations;
 };
 return 1;
}
API(replay_cursor_word) u32 replay_cursor_word(u32 index){return index<4?replay_cursor_sample[index]:~0u;}
API(replay_cursor_observed_callback) u32 replay_cursor_observed_callback(){return replay_cursor_sample_callback;}

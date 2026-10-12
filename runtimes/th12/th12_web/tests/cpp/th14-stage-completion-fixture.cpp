#include "../../cpp/game/ScoreFile.hpp"
#include "../../cpp/game/StageCompletion.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static GameEconomy economy;
static ClearRecords records;
static float rate=1;
struct Effects:StageCompletionEffects {
    u32 animations=0,recalls=0,fades=0;
    bool stage_result_animation()override{++animations;return true;}
    void recall_player_options()override{++recalls;}
    void start_ending_fade()override{++fades;}
};
static Effects effects;
static StageCompletion completion(economy,records,effects,&rate);
static ScoreFile scores;
static SpellRecords spells;
API(run) u32 run(i32 stage,i32 difficulty,i32 practice,i32 replay,i32 selection,i32 continues,i32 lives,i32 bombs,i32 score,i32 count,i32 clean){
    economy={};economy.score_units=score;economy.lives=lives;economy.th14_bombs=bombs;economy.difficulty=difficulty;
    records={};effects.animations=effects.recalls=0;
    records.clears[selection][difficulty]=count;records.no_continue_clears[selection][difficulty]=clean;
    for(u32 i=1;i<=48;++i)records.stages[selection][i][1]=0xa5;
    completion.mode={};completion.state={};completion.mode.stage=stage;completion.mode.selection=selection;completion.mode.continues=continues;
    completion.mode.control_mode=replay;completion.mode.replay_mode=replay;completion.mode.practice=practice&&!replay;completion.mode.replay_practice=practice&&replay;
    return completion.complete();
}
API(value) i32 value(u32 kind,u32 selection,u32 difficulty){
    switch(kind){case 0:return economy.score_units;case 1:return completion.state.displayed_bonus;
    case 2:return records.clears[selection][difficulty];case 3:return records.no_continue_clears[selection][difficulty];
    case 4:return i32(completion.state.exit);case 5:return completion.state.next_stage;
    case 6:return effects.animations;case 7:return effects.recalls;case 8:return completion.state.hud_flags;case 9:return completion.state.ending_active;default:return 0;}
}
API(pair) u32 pair(u32 selection,u32 index,u32 byte){return records.stages[selection][index][byte];}
API(serialized) const u8* serialized(u32 selection){
    scores.characters={};scores.write_records(spells,records);
    // Reload verifies the no-continue counters survive the real consumer.
    ClearRecords loaded;scores.read_records(spells,loaded);records=loaded;
    return scores.characters[selection].data();
}
API(clock_run) void clock_run(i32 frame,u32 replay,u32 force,u32 active){
    completion.state={};completion.mode={};effects.fades=0;
    completion.state.ending_frames=frame;completion.state.hud_flags=active?0x10:0;
    completion.state.ending_active=active;
    completion.mode.control_mode=replay;completion.mode.force_title=force;
    completion.update();
}
API(clock_value) i32 clock_value(u32 kind){
    return kind==0?completion.state.ending_frames:kind==1?i32(effects.fades):i32(completion.state.exit);
}
API(result_clock_run) void result_clock_run(u32 flags,i32 frame,float speed){
    rate=speed;completion.state={};completion.state.hud_flags=flags;completion.state.result_timer.set(frame,&rate);completion.update();
}
API(result_clock_value) u32 result_clock_value(u32 k){return k==0?u32(completion.state.result_timer.current):k==1?u32(completion.state.result_timer.previous):k==2?float_bits(completion.state.result_timer.fractional):completion.result_delay_elapsed();}

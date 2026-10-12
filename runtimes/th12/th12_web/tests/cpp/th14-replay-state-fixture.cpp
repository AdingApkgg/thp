#include "th14-replay-session-fixture.cpp"
#include "../../cpp/game/ShotFiles.hpp"
static ReplayStageState snapshot;static GameEconomy restored;static Rng gameplay,visual;
static ShtResource* power_sheet;
API(restore_snapshot) void restore_snapshot(const u8* p,u32 visual_calls,u32 first){
 snapshot={};restored={};visual.seed=0x5678;visual.calls=visual_calls;gameplay.seed=0x1234;gameplay.calls=97;
 snapshot.read(p);snapshot.restore(restored,gameplay,first!=0,&visual);
}
API(snapshot_word) u32 snapshot_word(u32 n){
 const u32 words[]={gameplay.seed,visual.seed,gameplay.calls,visual.calls,u32(restored.score_units),u32(restored.power),u32(restored.point_value),u32(restored.graze),u32(restored.th14_point_items),u32(restored.max_point_value),u32(restored.max_power),u32(restored.power_step),u32(restored.lives),u32(restored.life_fragments),u32(restored.th14_life_awards),u32(restored.th14_bombs),u32(restored.th14_bomb_fragments),u32(restored.th14_special_drop_count),u32(restored.th14_combo.total),u32(restored.th14_combo.count),u32(restored.th14_combo.timer),float_bits(restored.th14_combo.position.x),float_bits(restored.th14_combo.position.y),float_bits(restored.th14_combo.position.z),u32(snapshot.x),u32(snapshot.y),u32(snapshot.continues),u32(snapshot.th14_practice_mode),u32(snapshot.weapon)};
 if(n<sizeof words/sizeof *words)return words[n];n-=sizeof words/sizeof *words;if(n<28)return snapshot.th14_globals[n];return snapshot.spell_times[n-28];
}
API(initialize_power) i32 initialize_power(u32 selection,u32 raw){
 if(!session.begin(source,1,selection/2,selection%2,1))return 0;
 power_sheet=&session.resources.core.shots[shot_file_slot(selection/2,selection%2)];power_sheet->header.power_step=i32(raw);return session.battle->player->initialize();
}
API(power_word) u32 power_word(u32 n){const u32 words[]={u32(power_sheet->header.power_step),u32(session.economy.max_power),u32(session.economy.power_step)};return words[n];}
API(begin_counted_demo) i32 begin_counted_demo(u32 demo,u32 calls){session.animations.script_rng.seed=0x5678;session.animations.script_rng.calls=calls;return begin_demo(demo);}
API(visual_word) u32 visual_word(u32 n){return n?session.animations.script_rng.calls:session.animations.script_rng.seed;}

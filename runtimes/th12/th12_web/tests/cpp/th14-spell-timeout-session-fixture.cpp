#include "th14-startup-fixture.cpp"
API(timeout_clock) u32 timeout_clock(double now){return session.sample_spell_clock(now);}
API(timeout_state) u32 timeout_state(u32 field){
    if(!session.battle)return 0;
    const auto& b=*session.battle;
    const u32 values[]={b.spell_flags,u32(b.spells.frame_count),u32(b.spell_timing.last_frames),u32(b.spell_timing.encoded),b.spell_timing.index,
        u32(b.hud.show_spell_time),b.hud.spell_notice,b.hud.spell_time_animation,b.spell_timing.records[0],u32(b.th14_spell_result_requested),u32(b.game_over_requested),
        u32(session.spell_records.entries[b.spells.selection][b.spell_id].practice_captures),u32(session.spell_records.entries[b.spells.selection][b.spell_id].practice_attempts)};
    return values[field];
}

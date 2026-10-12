#include "th14-startup-fixture.cpp"
API(spell_clock_sample) u32 spell_clock_sample(double now){return session.sample_spell_clock(now);}
API(spell_clock_value) u32 spell_clock_value(u32 field){const auto& b=*session.battle;const u32 values[]={b.spell_flags,u32(b.spells.frame_count),u32(b.spell_timing.last_frames),u32(b.spell_timing.encoded),b.spell_timing.index,b.spell_timing.records[0],u32(b.hud.show_spell_time)};return values[field];}
API(spell_clock_end) u32 spell_clock_end(){auto& b=*session.battle;b.spell_flags=(b.spell_flags&~2u)|0x80;return b.spells.end()&&b.start_dialogue(-2);}
API(spell_clock_start) double spell_clock_start(){return session.battle->spell_timing.start;}
API(spell_clock_saved_time) u32 spell_clock_saved_time(){Replay r;if(!r.open(saved_replay.data(),saved_replay.size()))return 0;ReplayStageState entry;const auto* p=r.header(session.state.stage);if(!p)return 0;entry.read(p);return entry.spell_times[0];}

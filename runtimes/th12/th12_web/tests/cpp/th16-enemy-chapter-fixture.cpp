#include "../../cpp/game/EnemyManager.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static EnemyState e;static EnemyEnvironment env;static EnemyCommandEnvironment w;
API(erase) i32 erase(u32 flags){
 e={};e.flags=flags;e.drops.primary=50;for(u32 n=0;n<17;++n)e.drops.counts[n]=51+n;e.drops.spread={float_bits(68u),float_bits(69u)};e.th16_death_reference={1,2};e.th16_chapter_credit=7;
 const bool selected=enemy_th16_clear_drops(e);if(selected)e.flags|=0x2000000;return selected;
}
API(erase_value) u32 erase_value(u32 n){if(!n)return e.flags;if(n==1)return u32(e.drops.primary);if(n<19)return u32(e.drops.counts[n-2]);if(n==19)return float_bits(e.drops.spread.x);if(n==20)return float_bits(e.drops.spread.y);if(n==21)return float_bits(e.th16_death_reference.x);if(n==22)return float_bits(e.th16_death_reference.y);return u32(e.th16_chapter_credit);}
API(chapter) i32 chapter(i32 tag,i32 credit){
 e={};e.th16_chapter_tag=w.stage_section=w.th16_game_chapter=9;e.th16_chapter_credit=credit;
 alignas(4) u8 bytes[20]{};auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=524;cmd->length=20;std::memcpy(bytes+16,&tag,4);EclContext c;c.instruction=cmd;EnemyScriptServices services(e,env,w);return services.command(c);
}
API(chapter_value) u32 chapter_value(u32 n){return n==0?u32(w.stage_section):n==1?u32(w.th16_game_chapter):n==2?u32(e.th16_chapter_tag):u32(e.th16_chapter_credit);}
API(death) void death(i32 tag,i32 chapter,i32 credit){e={};e.th16_chapter_tag=tag;e.th16_chapter_credit=credit;w.stage_section=chapter;w.th16_chapter_removed=INT32_MAX;enemy_th16_chapter_death(e,w);}
API(death_value) u32 death_value(u32 n){return n?u32(w.th16_chapter_removed):u32(e.th16_chapter_credit);}
API(credit) i32 credit(i32 tag,i32 chapter,i32 amount){e={};e.th16_chapter_tag=tag;e.th16_chapter_credit=amount;w.stage_section=chapter;w.th16_chapter_removed=INT32_MAX;EclInstruction cmd{};cmd.opcode=570;EclContext c;c.instruction=&cmd;EnemyScriptServices services(e,env,w);return services.command(c);}
API(setting) i32 setting(i32 credit,i32 value,i32 spawned){
 e={};e.th16_chapter_credit=credit;w.th16_chapter_spawned=spawned;
 alignas(4) u8 bytes[20]{};auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=569;cmd->length=20;std::memcpy(bytes+16,&value,4);EclContext c;c.instruction=cmd;EnemyScriptServices services(e,env,w);return services.command(c);
}
API(setting_value) u32 setting_value(u32 n){return n?u32(w.th16_chapter_spawned):u32(e.th16_chapter_credit);}
API(timer_case) i32 timer_case(u32 flags,float rate){
 e={};env.rate=rate;e.th16_phase_timer.previous=19;e.th16_phase_timer.current=20;e.th16_phase_timer.fractional=20.5f;e.th16_phase_timer.flags=flags;e.th16_phase_timer.rate=(flags&1)?&env.rate:nullptr;
 EclInstruction cmd{};cmd.opcode=513;EclContext c;c.instruction=&cmd;EnemyScriptServices services(e,env,w);return services.command(c);
}
API(timer_tick) void timer_tick(){e.th16_phase_timer.tick();}
API(timer_word) u32 timer_word(u32 n){const auto& t=e.th16_phase_timer;const u32 words[]={u32(t.previous),u32(t.current),float_bits(t.fractional),t.rate?1u:0u,t.flags};return words[n];}

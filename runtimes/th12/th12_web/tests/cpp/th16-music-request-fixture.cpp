#include "../../cpp/game/GameSession.hpp"
#include "../../cpp/game/MusicCatalog.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static GameResources source;
static GameSession session;
static u32 before,after;
static Dialogue* old_dialogue;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(open_archive) i32 open_archive(const u8* p,u32 n){return source.open_archive(p,n);}
API(begin) i32 begin(){return session.begin(source,1,0,0,1);}
API(cue) i32 cue(i32 stage,i32 boss){return stage_music(stage,boss);}
API(logo) i32 logo(i32 mode,u32 flags){
 auto& b=*session.battle;b.enemy_commands.th16_runtime_mode=mode;b.enemy_commands.th16_run_flags=flags;
 before=anm_creation_count();EclInstruction cmd{};cmd.opcode=554;EclContext c;c.instruction=&cmd;
 EnemyState enemy{};EnemyScriptServices services(enemy,b.enemy_environment,b.enemy_commands);const auto result=services.command(c);after=anm_creation_count();return result;
}
API(request) i32 request(i32 stage,i32 id,i32 existing){
 auto& b=*session.battle;session.resources.stage_number=stage;b.events.clear();
 b.dialogue->active=existing;b.dialogue->state.release_signal=37;old_dialogue=b.dialogue.get();
 b.enemy_commands.stage_section=123;b.enemy_commands.section_frame=456;
 before=anm_creation_count();const auto result=b.start_dialogue(id);after=anm_creation_count();return result;
}
API(value) i32 value(u32 n){auto& b=*session.battle;switch(n){
 case 0:return b.events.size();case 1:return b.events.empty()?-1:i32(b.events[0].kind);
 case 2:return b.events.empty()?-1:b.events[0].value;case 3:return after-before;
 case 4:return anm_creation_value(before,0);case 5:return anm_creation_value(before,1);
 case 6:return b.dialogue.get()==old_dialogue;case 7:return b.dialogue->active;
 case 8:return b.dialogue->state.release_signal;case 9:return b.enemy_commands.stage_section;
 case 10:return b.enemy_commands.section_frame;default:return -1;
}}

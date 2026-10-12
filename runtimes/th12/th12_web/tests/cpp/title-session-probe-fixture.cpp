#include "../../cpp/game/GameSession.hpp"
#include "../../cpp/game/EclTrap.hpp"
#include "../../cpp/game/PortTitle.hpp"
#include "../../cpp/game/Trace.hpp"
#include "render-fixture.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static GameResources source;
static GameSession session;
static test::RecordingGraphics graphics;
static AnmRenderer renderer(graphics);
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(open_archive) i32 open_archive(const u8* p,u32 n){return source.open_archive(p,n);}
API(build_title) u32 build_title(){return kPortTitle;}
API(begin) i32 begin(u32 stage,u32 character,u32 subtype,u32 difficulty){return session.begin(source,stage,character,subtype,difficulty);}
API(tick) i32 tick(u32 held){return session.update({held});}
API(tick_input) i32 tick_input(u32 held,i32 pause){GameSessionInput input;input.held=held;input.pause=pause!=0;return session.update(input);}
API(pause_value) i32 pause_value(u32 n){
 if(!session.pause_menu)return -1;const auto& m=*session.pause_menu;
 switch(n){case 0:return m.state;case 1:
#if PORT_TITLE == 16
 return m.th16_substate;
#else
 return m.state;
#endif
 case 2:return m.cursor.selected;case 3:return m.timer.current;default:return m.cursor.depth;}
}
API(draw) i32 draw(){graphics.data.clear();graphics.submissions.clear();graphics.snapshots.clear();graphics.target_events.clear();return session.draw(renderer);}
API(error) const char* error(){return session.error.c_str();}
API(last_file) const char* last_file(){return last_resource.c_str();}
API(phase) u32 phase(){return u32(session.state.phase);}
API(bullet_error) i32 bullet_error(){return session.battle?session.battle->bullets.last_error:-1;}
API(opcode_count) u32 opcode_count(u32 op){return ecl_opcode_count(op);}
API(bullet_transform) i32 bullet_transform(u32 n){
#if PORT_TITLE == 16
 if(session.battle){const auto* b=session.battle->bullets.first_th16();if(b&&n<18)return b->th16_transforms[n].opcode;}
#else
 (void)n;
#endif
 return -1;
}
API(value) u32 value(u32 n){switch(n){case 0:return session.state.stage;case 1:return session.state.frame;case 2:return g_ecl_last_opcode;case 3:return session.animations.last_error;default:return graphics.submissions.size();}}
API(battle_value) i32 battle_value(u32 n){if(!session.battle)return -1;auto& b=*session.battle;
 switch(n){case 0:return b.enemies.count;case 1:return b.enemies.total_created;case 2:return b.enemy_commands.stage_section;
 case 3:return b.damage_total;case 4:return ecl_opcode_count(518);case 5:return ecl_opcode_count(519);case 6:return ecl_opcode_count(520);
 case 7:return b.dialogue&&b.dialogue->active;case 8:return b.dialogue?b.dialogue->state.release_signal:-1;case 9:return b.player_live;
 default:return ecl_update_total();}
}

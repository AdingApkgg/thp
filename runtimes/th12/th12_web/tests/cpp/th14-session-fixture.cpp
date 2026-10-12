#include "../../cpp/game/GameSession.hpp"
#include "../../cpp/game/EclTrap.hpp"
#include "../../cpp/game/Trace.hpp"
#include "render-fixture.hpp"
#include <cstdlib>
#include <cstdio>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static GameResources source;
static GameSession session;
static th11::test::RecordingGraphics graphics;
static AnmRenderer renderer(graphics);
static bool long_recording=false;
static u32 recording_chunks=0;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(open_archive) i32 open_archive(const u8* p,u32 n){return source.open_archive(p,n);}
API(begin) i32 begin(u32 stage,u32 character,u32 subtype,u32 difficulty){recording_chunks=0;g_th14_bullet_unhandled=0;g_th14_bullet_unsupported_native=0;return session.begin(source,stage,character,subtype,difficulty);}
API(bullet_skipped_mask) u32 bullet_skipped_mask(){return g_th14_bullet_unhandled;}
API(bullet_unsupported_native_mask) u32 bullet_unsupported_native_mask(){return g_th14_bullet_unsupported_native;}
API(allow_long_recording) void allow_long_recording(u32 value){long_recording=value!=0;}
API(recording_chunk_count) u32 recording_chunk_count(){return recording_chunks;}
API(tick) i32 tick(u32 held){return session.update({held});}
// Diagnostic isolation only: hold player invulnerability while exercising
// the original stage scripts. Production gameplay never calls this export.
API(combat_tick) i32 combat_tick(u32 held){
    // Diagnostic long runs discard recorder-only chunks; game/ECL clocks
    // and production recorder limits are unchanged. These runs cannot be
    // used to validate replay saving or replay equivalence.
    if(long_recording&&session.recording.selected){auto& r=session.recording.stages[session.recording.selected];if(r.frames>=86000){r.frames=0;r.inputs.clear();r.fps.clear();r.touches.clear();++recording_chunks;}}
    if(session.battle&&session.battle->player)session.battle->player->state.invincibility.set(120,&session.animations.rate);return session.update({held});
}
API(phase) u32 phase(){return u32(session.state.phase);}
API(stage_exit) u32 stage_exit(){return session.battle?u32(session.battle->completion.state.exit):0;}
API(completed_result) i32 completed_result(){return session.pause_menu?session.pause_menu->completed:0;}
API(draw) i32 draw(){graphics.data.clear();graphics.submissions.clear();graphics.snapshots.clear();graphics.target_events.clear();return session.draw(renderer);}
API(error) const char* error(){return session.error.c_str();}
API(laser_diagnostic) i32 laser_diagnostic(u32 n){
    if(!session.battle)return 0;
    for(auto* b=session.battle->lasers.first();b;b=b->next)if(b->type==0){
        const auto& l=*reinterpret_cast<Th14LaserLine*>(b);if(!l.diagnostic)continue;
        u32 opcode=0;if(b->transform_index>=0&&b->transform_index<18)std::memcpy(&opcode,l.request+0x34+b->transform_index*0x2c+0x20,4);
        switch(n){case 0:return l.diagnostic;case 1:return b->transform_index;case 2:return i32(opcode);case 3:return b->lifetime.current;case 4:return b->id;default:return 0;}
    }
    for(auto* b=session.battle->lasers.first();b;b=b->next)if(b->type==1){
        auto& l=*reinterpret_cast<Th14LaserInfinite*>(b);if(!l.diagnostic)continue;
        switch(n){case 0:return l.diagnostic;case 1:return b->transform_index;case 2:return b->state;case 3:return b->lifetime.current;case 4:return b->id;default:return 0;}
    }
    for(auto* b=session.battle->lasers.first();b;b=b->next)if(b->type==2){
        auto& curve=*reinterpret_cast<Th14LaserCurve*>(b);if(!curve.diagnostic)continue;
        const i32 index=curve.path.transform_index;u32 opcode=0;if(index>=0&&index<18)std::memcpy(&opcode,curve.path.request+0x2c+index*0x2c+0x20,4);
        switch(n){case 0:return curve.diagnostic;case 1:return index;case 2:return i32(opcode);case 3:return curve.curve_timer.current;case 4:return i32(curve.path.samples.size());default:return 0;}
    }return 0;
}
API(last_file) const char* last_file(){return last_resource.c_str();}
API(anm_error) u32 anm_error(){return session.animations.last_error;}
API(item_collect_type) i32 item_collect_type(){return session.battle?session.battle->items.th14_last_collect_type:-1;}
API(ecl_diagnostic) const char* ecl_diagnostic(){
 static char text[256];const auto* p=ecl_last_integer_access;
 std::snprintf(text,sizeof text,"trace=%d accessOpcode=%u argument=%d refs=%x args=%08x,%08x clamps=%d",i32(trace_point),p?p->opcode:0,ecl_last_integer_argument,p?p->references:0,p&&p->length>=20?p->argument<u32>(0):0,p&&p->length>=24?p->argument<u32>(1):0,ecl_stack_clamp_count);return text;
}
API(creation_count) u32 creation_count(){return anm_creation_count();}
API(creation) i32 creation(u32 n,u32 k){return anm_creation_value(n,k);}
API(enemy_error) const char* enemy_error(){
    static char text[256];text[0]=0;if(!session.battle)return text;
    const auto* failed=session.battle->enemies.script_error.instruction;if(!failed)return text;
    std::snprintf(text,sizeof text,"opcode=%u args=%08x,%08x refs=%x",failed->opcode,failed->argument<u32>(0),failed->length>=24?failed->argument<u32>(1):0,failed->references);
    for(auto* node=session.battle->enemies.first;node;node=node->next){auto& e=*node->value;
        if(e.script.root.instruction==failed||(e.script.active&&e.script.active->instruction==failed)){
            const i32 file=e.state.animation_file;const auto* resource=u32(file)<16?session.battle->enemy_animations.resources[file].file:nullptr;
            const auto& context=e.script.active?*e.script.active:e.script.root;u32 local=0;
            if(context.stack.frame_base>=0&&u32(context.stack.frame_base)+4<=sizeof context.stack.data)std::memcpy(&local,context.stack.data+context.stack.frame_base,4);
            std::snprintf(text,sizeof text,"file=%d scripts=%u args=%08x,%08x refs=%x id=%d parent=%u frame_base=%d local0=%08x",file,resource?u32(resource->scripts.size()):0,failed->argument<u32>(0),failed->length>=24?failed->argument<u32>(1):0,failed->references,e.state.instance_id,e.state.parent_instance_id,context.stack.frame_base,local);break;
        }
    }return text;
}
API(value) u32 value(u32 k){switch(k){case 0:return session.state.frame;case 1:return session.state.stage;case 2:return g_ecl_last_opcode;case 3:return session.animations.active_count();default:return graphics.submissions.size();}}
API(player_diagnostic) i32 player_diagnostic(u32 n){
    if(!session.battle||!session.battle->player)return -1;const auto& p=*session.battle->player;
    switch(n){case 0:return p.last_error;case 1:return p.motion.last_error;case 2:return p.shots.last_error;case 3:return p.state.life_state;case 4:return p.state.state_timer.current;case 5:return p.shots.player.bomb_active;case 6:return p.shots.player.special_active;case 7:{i32 count=0;for(const auto& a:p.shots.damage_areas.areas)if(a.flags&1)++count;return count;}default:return p.state.invincibility.current;}
}
API(progression_diagnostic) const char* progression_diagnostic(){
 static std::string text;text.clear();if(!session.battle)return "";auto& b=*session.battle;char row[512];
 if(b.player){auto& p=*b.player;u32 live=0;for(u32 j=0;j<256;++j)if(p.shots.at(j).state)++live;
  std::snprintf(row,sizeof row,"held=%x shots=%u power=%d dialogue=%d blocked=%u/%d hud=%x section=%d pos=%.3f,%.3f; ",p.shots.player.held,live,p.shots.player.power,b.dialogue&&b.dialogue->active,p.shots.player.th14_shooting_blocked,p.shots.player.th14_dialogue_blocked,b.completion.state.hud_flags,b.enemy_commands.stage_section,p.motion.state.position.x,p.motion.state.position.y);text+=row;}
 u32 n=0;for(auto* node=b.enemies.first;node&&n<20;node=node->next,++n){auto& e=*node->value;auto& s=e.state;
  std::snprintf(row,sizeof row,"id=%d flags=%x hp=%d/%d hitbox=%.3f,%.3f pos=%.3f,%.3f age=%d phaseClock=%d immunity=%d rootTime=%.3f opcode=%u interrupts=",s.instance_id,s.flags,s.health,s.max_health,s.hitbox.x,s.hitbox.y,s.current.position.x,s.current.position.y,s.lifetime.current,s.timer_2bc.current,s.damage_immunity.current,e.script.root.time,e.script.root.instruction?e.script.root.instruction->opcode:0);text+=row;
  for(const auto& i:s.interrupts)if(i.health_script||i.timeout_script){std::snprintf(row,sizeof row,"[%d,%d,%s,%s]",i.health,i.time,i.health_script?i.health_script:"-",i.timeout_script?i.timeout_script:"-");text+=row;}text+="; ";
 }return text.c_str();
}
API(enemy_drop) i32 enemy_drop(u32 n){
    if(!session.battle)return -1;const auto* failed=session.battle->enemies.script_error.instruction;
    for(auto* node=session.battle->enemies.first;node;node=node->next){auto& e=*node->value;
        if(e.script.root.instruction==failed||(e.script.active&&e.script.active->instruction==failed))
            return n==0?e.state.drops.primary:n<=13?e.state.drops.counts[n-1]:session.battle->items.last_error;
    }return -1;
}
API(enemy_laser_request) u32 enemy_laser_request(u32 n){
    if(!session.battle||n>=0x374/4)return 0;
    const auto* failed=session.battle->enemies.script_error.instruction;
    for(auto* node=session.battle->enemies.first;node;node=node->next){auto& e=*node->value;
        if(e.script.root.instruction==failed||(e.script.active&&e.script.active->instruction==failed)){
            u32 value;std::memcpy(&value,e.state.th14_request.bytes+n*4,4);return value;
        }
    }return 0;
}

// Diagnostic outputs only. No original RNG values enter the engine.
#include "th14-perspective-rep-split-fixture-nov05.cpp"
namespace {
struct ScriptRegisterAudit {
 u32 first=0,last=0,count=0,overflow=0;bool installed=false;
 std::array<std::array<u32,16>,4096> rows{};
} script_register_audit;
void record_script_register(const AnmVm* vm,Rng& rng,RngBoundary point){
 auto& audit=script_register_audit;
 if(!audit.installed||public_player_observations<audit.first||public_player_observations>audit.last)return;
 if(point!=RngBoundary::SeedRead&&point!=RngBoundary::SeedWritten)return;
 const u32 role=&rng==&session.animations.script_rng?0:&rng==&session.animations.visual_rng?1:2;
 if(role==2)return;
 if(audit.count==audit.rows.size()){++audit.overflow;return;}
 const auto* battle=session.battle.get();
 audit.rows[audit.count++]={public_player_observations,session.state.stage,u32(point),role,rng.seed,rng.calls,
  vm?u32(vm->file_index):~0u,vm?u32(i32(vm->script_index)):~0u,vm?vm->flags2:0,
  battle?battle->pending_stage:0,battle?u32(battle->stage_loader.phase):0,
  battle?u32(battle->stage_loader.initializing):0,battle?u32(battle->stage_loader.preparing_scene):0,
  session.animations.depth(),u32(probe_clock_ns),u32(probe_clock_ns>>32)};
}
struct OuterRegisterAudit {
 RngBoundaryScope scope;
 OuterRegisterAudit():scope(session.animations.script_rng,session.animations.visual_rng,nullptr,
  [](void*,Rng& rng,RngBoundary point){record_script_register(nullptr,rng,point);return true;}){}
};
}
API(rng_audit_install) u32 rng_audit_install(u32 first,u32 last){
 auto& audit=script_register_audit;
 if(audit.installed||public_player_observations!=1||!first||last<first)return 0;
 audit.installed=true;audit.first=first;audit.last=last;
 static auto previous=session.animations.before_rng_boundary;
 session.animations.before_rng_boundary=[](const AnmVm& vm,Rng& rng,RngBoundary point){
  // SeedRead is after the local input load; capture before a downstream
  // readiness callback can publish another seed. SeedWritten is analogous.
  record_script_register(&vm,rng,point);
  return !previous||previous(vm,rng,point);
 };
 return 1;
}
API(rng_audit_menu_tick) u32 rng_audit_menu_tick(u64 now,u32 held){OuterRegisterAudit audit;return menu_tick(now,held);}
API(rng_audit_draw) u32 rng_audit_draw(){OuterRegisterAudit audit;return draw();}
API(rng_audit_meta) u32 rng_audit_meta(u32 index){const auto& a=script_register_audit;const u32 values[]={a.first,a.last,a.count,a.overflow,u32(a.installed)};return index<5?values[index]:~0u;}
API(rng_audit_word) u32 rng_audit_word(u32 row,u32 word){const auto& a=script_register_audit;return row<a.count&&word<16?a.rows[row][word]:~0u;}

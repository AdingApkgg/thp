#include "th16-options-session-fixture.cpp"
API(begin_stage_season) i32 begin_stage_season(u32 stage,u32 character,u32 season,u32 difficulty){
 if(season>=5||!session.begin(source,stage,character,0,difficulty))return 0;
 auto& player=*session.battle->player;session.economy.th16_subseason=season;
 player.th16_season_shots=&session.resources.core.season_shots[season];player.th16_season_animation=&session.resources.core.season_players[season];
 return player.rebuild_th16_options();
}
// Diagnostic coverage only. This is not part of production gameplay.
API(coverage_invincibility) void coverage_invincibility(){if(session.battle&&session.battle->player)session.battle->player->state.invincibility.set(600,&session.animations.rate);}
API(begin_demo) i32 begin_demo(u32 index){if(index>=4)return 0;std::vector<u8> bytes;char name[20];std::snprintf(name,sizeof name,"demo%u.rpy",index+1);return source.read(name,bytes)&&session.begin_replay(source,bytes.data(),u32(bytes.size()),0,true);}
API(trace_code) i32 trace_code(){return trace_point;}
// Resolve addresses before stepping; traps invalidate subsequent calls into WASM.
namespace th11 {extern const EclInstruction* ecl_last_integer_access;extern i32 ecl_last_integer_argument;}
API(trace_address) const volatile i32* trace_address(){return &trace_point;}
API(last_instruction_address) const EclInstruction* const* last_instruction_address(){return &ecl_last_integer_access;}
API(last_argument_address) const i32* last_argument_address(){return &ecl_last_integer_argument;}
API(resource_slot_valid) i32 resource_slot_valid(u32 n){if(!session.battle||n>=4)return 0;const auto& slot=session.battle->enemy_animations.resources[n+2];const auto& stage=*session.resources.stage;return slot.file==(stage.ecl_animation_names[n].empty()?nullptr:&stage.ecl_animations[n])&&slot.id==10+n;}
API(resource_name) const char* resource_name(u32 n){return n<4?session.resources.stage->ecl_animation_names[n].c_str():"";}
namespace th11 {extern i32 th16_collect_failure;extern u32 th16_collect_source;}
API(battle_diagnostic) i32 battle_diagnostic(u32 n){auto& b=*session.battle;switch(n){case 0:return b.items.last_error;case 1:return b.player->shots.last_error;case 2:return b.animations.last_error;case 3:return b.enemies.script_error.opcode;case 4:return th16_collect_failure;case 5:return th16_collect_source;default:return b.player->shots.player.bomb_active;}}
API(damage_source_word) u32 damage_source_word(u32 id,u32 n){return id<=256&&n<37?session.battle->player->shots.th16_sources.records[id].words[n]:0;}
API(source_shot_word) u32 source_shot_word(u32 id,u32 n){if(id>=256)return 0;const auto& state=session.battle->player->shots.at(id);const auto& shot=state.th16;auto* vm=session.animations.find(shot.animation);switch(n){case 0:return state.state;case 1:return state.spec?state.spec->extra_callback:0xffffffff;case 2:return shot.animation;case 3:return !!vm;case 4:return vm?vm->th16_callbacks[3]:0xffffffff;default:return shot.damage_source;}}
API(spawn_failure) i32 spawn_failure(){return session.battle->enemies.th16_spawn_failure;}
API(failed_spawn_name) const char* failed_spawn_name(){return session.battle->enemies.th16_failed_spawn;}
API(frame_failure_word) i32 frame_failure_word(u32 n){return n<15?session.battle->enemies.th16_frame_failure[n]:0;}
API(script_error_address) const EclInstruction* script_error_address(){return session.battle->enemies.script_error.instruction;}
API(failed_laser_request_word) u32 failed_laser_request_word(u32 index,u32 word){if(index>=16||word>=0x358/4)return 0;auto& manager=session.battle->enemies;for(auto* node=manager.first;node;node=node->next)if(node->value->state.instance_id==u32(manager.th16_frame_failure[1])){u8 request[0x358]{};if(enemy_th16_laser_request(node->value->state,index,request)){u32 value;std::memcpy(&value,request+word*4,4);return value;}}return 0;}

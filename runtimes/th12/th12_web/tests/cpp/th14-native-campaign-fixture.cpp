// TH14 headless campaign observation with explicit host timing inputs.
// Test adapter only: no GPU/audio claim, native state injection or per-frame corrections.
static void capture_mid_live();

static void capture_combat_checkpoint();

static unsigned camera_words[25]{},camera_creation_count=0,hud_words[2]{};


// Composed diagnostic adapter: e2ebfc6f55-fixture.cpp

// Composed diagnostic adapter: 21a4b2bf9c-69d5982339-fixture.cpp

// Composed diagnostic adapter: 457127a70e-e7c2bf0413-th14-public-replay-physical-fixture.cpp

// Composed diagnostic adapter: 9739aeeade-4aced5ae45-th14-custom-replay-reference-fixture.cpp

// Composed diagnostic adapter: 1022e478a1-d176065070-th14-session-reference-fixture.cpp

// Composed diagnostic adapter: 6ffcbad392-1827f4345e-th14-replay-session-fixture.cpp

// Composed diagnostic adapter: d6cff39822-ab3759c5d9-th14-session-fixture.cpp
#include "GameSession.hpp"
#include "EclTrap.hpp"
#include "Trace.hpp"

// Composed diagnostic adapter: 201d6df71d-0fca245a01-render-fixture.hpp
#pragma once

#include "AnmRenderer.hpp"


namespace th11::test {



struct RecordingGraphics final:ZunGraphics {



    touhou::graphics::PipelineState state{};std::vector<u8> data;



    u32 calls=0,texture_id=0,layout=0;



    Matrix4 world{},uv{};u32 topology=0;



    struct TargetEvent {u32 kind,target,color,count;GraphicsViewport rectangle;};



    std::vector<TargetEvent> target_events;u32 target=0;GraphicsViewport viewport;



    struct Submission {u32 target,texture,start,size,topology,count,stride;};



    std::vector<Submission> submissions;



    struct Snapshot {u32 depth_write,depth_compare,fog,layout,factor;Matrix4 world,uv;};



    std::vector<Snapshot> snapshots;



    void snapshot(){snapshots.push_back({state.depthWrite,u32(state.depthCompare),state.fog,layout,state.textureFactor,world,uv});}



    bool select_target(const AnmResource* file,u32 index)override{target=file?index+1:0;viewport={};target_events.push_back({0,target,0,0,{}});return true;}



    // The port gave the virtual a third, defaulted parameter (flags); an override that omits it stops



    // being an override. The parameter is unnamed here because the fixture records the call, and the



    // shape of its event record is read by the suites.



    bool clear_target(u32 color,const GraphicsViewport* rect,u32)override{target_events.push_back({1,target,color,rect?1u:0u,rect?*rect:viewport});return true;}



    void set_viewport(const GraphicsViewport& v)override{viewport=v;}



    touhou::graphics::PipelineState& pipeline()override{return state;}



    u32 texture(const AnmResource&,u32 index)override{return index+1;}



    void bind_texture(u32 handle)override{texture_id=handle;}



    void set_layout(touhou::graphics::VertexLayout v)override{layout=u32(v);}



    void set_matrix(touhou::graphics::MatrixKind kind,const Matrix4& m)override{if(kind==touhou::graphics::MatrixKind::World)world=m;if(kind==touhou::graphics::MatrixKind::Texture)uv=m;}



    void triangles(u32 n,const void* v,u32 stride)override{++calls;snapshot();submissions.push_back({target,texture_id,u32(data.size()),n*3*stride,3,n,stride});const auto* b=static_cast<const u8*>(v);data.insert(data.end(),b,b+n*3*stride);}



    void primitives(touhou::graphics::Topology t,u32 n,const void* v,u32 stride)override{++calls;snapshot();topology=u32(t);const u32 size=touhou::graphics::vertex_count(t,n)*stride;submissions.push_back({target,texture_id,u32(data.size()),size,u32(t),n,stride});const auto* b=static_cast<const u8*>(v);data.insert(data.end(),b,b+size);}



};



struct RenderFixture {RecordingGraphics graphics;AnmRenderer renderer{graphics};AnmResource resource;AnmSprite sprite;};



}







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







static std::vector<u8> original_replay,saved_replay;



API(begin_demo) i32 begin_demo(u32 index){



 if(index>=3)return 0;char name[20];std::snprintf(name,sizeof name,"demo%u.rpy",index);



 return source.read(name,original_replay)&&session.begin_replay(source,original_replay.data(),u32(original_replay.size()),0,true);



}



API(replay_observation) i32 replay_observation(u32 n){



 const auto& r=session.playback;const auto* stage=r.stage(session.state.stage);



 const u32 selection=replay_selection;u32 raw[4]{};



 if(r.decoded().size()>=selection+16)std::memcpy(raw,r.decoded().data()+selection,16);



 switch(n){case 0:return session.state.character;case 1:return session.state.subtype;case 2:return session.state.difficulty;



 case 3:return session.state.stage;case 4:return stage?stage->frames:0;case 5:return r.frame();



 case 6:case 7:case 8:case 9:return raw[n-6];



 case 10:return session.economy.lives;case 11:return session.economy.power;case 12:return session.economy.th14_bombs;



 case 13:return session.animations.script_rng.seed;case 14:return session.animations.script_rng.calls;



 case 15:return session.economy.score_units;case 16:return session.economy.graze;



 case 17:return session.battle&&session.battle->player?session.battle->player->motion.state.x:0;



 case 18:return session.battle&&session.battle->player?session.battle->player->motion.state.y:0;



 default:return 0;}



}







static u32 reference[32]{};



static u32 reference_rewards[3]{};



static u32 reference_next_id_value=0;



static u32 reference_popup_cursor_value=0;



static std::array<u32,324> reference_popups{};



namespace th11 {extern const EclInstruction* ecl_last_integer_access;}



static std::vector<u32> reference_rng_reads;



static void observe_rng_read(i32 id,i32 enemy,u32 calls){



 if(!((calls>=3326&&calls<3334)||(calls>=12660&&calls<12690)))return;



 const auto* inst=ecl_last_integer_access;



 const u32 row[]={calls,u32(id),u32(enemy),inst?u32(inst->opcode):0,inst?u32(inst->time):0,inst?u32(inst->references):0,



  inst&&inst->length>=20?inst->argument<u32>(0):0,inst&&inst->length>=24?inst->argument<u32>(1):0};



 reference_rng_reads.insert(reference_rng_reads.end(),std::begin(row),std::end(row));



}



static std::vector<u32> reference_shots,reference_enemies,reference_phases,reference_items,reference_bullets,reference_areas,reference_ids;



static u32 float_word(float x){u32 out;std::memcpy(&out,&x,4);return out;}



static void observe_reference(const GameBattle& b){



 reference_popup_cursor_value=b.popups.cursor;



 for(u32 n=0;n<18;++n){const auto& popup=n<13?b.popups.entries[n]:b.popups.bonuses[n-13];



  std::memcpy(reference_popups.data()+n*18,&popup,sizeof(popup));



  reference_popups[n*18+11]=popup.age.rate?1:0;



 }



 reference_next_id_value=b.enemies.total_created;



 const auto& p=*b.player;const auto& e=b.economy;



 u32 live=0;for(u32 n=0;n<256;++n)if(p.shots.at(n).state)++live;



 // Retail's rate-scaled controller clock has advanced at priority11;



 // physical Replay frame ordinals are separate and do not repeat.



 const i32 fields[]={b.control_frame(),i32(p.input.movement.held),i32(p.input.movement.pressed),



  p.motion.state.x,p.motion.state.y,p.state.life_state,p.state.state_timer.current,



  p.state.transition_timer.current,p.state.th14_shooting_age.current,p.state.invincibility.current,



  p.shots.schedule.timer.current,p.motion.state.weapon_mode,



  e.score_units,e.graze,e.point_value,e.power,e.lives,e.life_fragments,e.th14_bombs,e.th14_bomb_fragments,e.rank,



  i32(b.animations.script_rng.seed),i32(b.animations.script_rng.calls),



  i32(b.animations.visual_rng.seed),i32(b.animations.visual_rng.calls),i32(b.enemies.count),i32(live),



  session.state.character,session.state.subtype,session.state.difficulty,i32(session.state.stage),i32(p.th14_scale.flags)};



 for(u32 n=0;n<32;++n)reference[n]=u32(fields[n]);



 reference_rewards[0]=p.shots.player.th14_plain_hits;reference_rewards[1]=p.shots.player.th14_focused_hits;reference_rewards[2]=p.shots.player.th14_hits_184bc;



 reference_ids.clear();for(auto* node=b.enemies.first;node;node=node->next)reference_ids.push_back(u32(node->value->state.instance_id));



 reference_shots.clear();reference_enemies.clear();reference_phases.clear();



 if(reference[30]==3&&reference[0]>=7075&&reference[0]<=7240){



  for(u32 n=0;n<256;++n){const auto& s=p.shots.at(n);if(!s.state)continue;



   const auto* area=s.spec&&s.spec->type==3?p.shots.th14_bomb_area(s.th14_area_slot):nullptr;



   const u32 row[]={n,u32(s.state),u32(s.timer.current),u32(s.damage),



    float_word(s.movement.position.x),float_word(s.movement.position.y),float_word(s.movement.position.z),



    float_word(s.movement.speed),float_word(s.movement.angle),float_word(area?area->size.x:(s.spec?s.spec->hitbox.x:0)),float_word(area?area->size.y:(s.spec?s.spec->hitbox.y:0))};



   reference_shots.insert(reference_shots.end(),std::begin(row),std::end(row));



  }



  for(auto* node=b.enemies.first;node;node=node->next){const auto& s=node->value->state;



   const u32 row[]={u32(s.health),u32(s.max_health),s.flags,float_word(s.current.position.x),float_word(s.current.position.y),



    float_word(s.hitbox.x),float_word(s.hitbox.y),float_word(s.collision_box.x),float_word(s.collision_box.y),u32(s.lifetime.current)};



   reference_enemies.insert(reference_enemies.end(),std::begin(row),std::end(row));



   reference_phases.push_back(u32(s.timer_2bc.current));reference_phases.push_back(u32(s.drops.primary));



   for(u32 n=0;n<13;++n)reference_phases.push_back(u32(s.drops.counts[n]));



   for(const auto& interrupt:s.interrupts)reference_phases.push_back(u32(interrupt.health));



  }



 }



 reference_areas.clear();



 if(reference[30]==3&&reference[0]>=7075&&reference[0]<=7240){



  for(u32 j=0;j<256;++j){const auto* a=p.shots.th14_bomb_area(j);if(!(a->flags&1))continue;



   const ShotState* owner=p.shots.th14_area_owner(j);



   const u32 row[]={j,a->flags,float_word(a->radius),float_word(a->angle),float_word(a->size.x),float_word(a->size.y),



    float_word(a->position.x),float_word(a->position.y),float_word(a->position.z),u32(a->timer.previous),u32(a->timer.current),float_word(a->timer.fractional),



    u32(a->damage),u32(a->total),u32(a->maximum),u32(a->period),a->stamp,u32(a->callback!=0),owner?u32(owner->timer.current):0,owner?owner->th14_shot_flags:0};



   reference_areas.insert(reference_areas.end(),std::begin(row),std::end(row));



  }



 }



 reference_bullets.clear();



 if(reference[0]<=350){



  for(auto* s=b.bullets.first_th14();s;s=s->th14_active_next){



   const u32 row[]={u32(s->state),s->flags,u32(s->collision_delay),float_word(s->position.x),float_word(s->position.y),float_word(s->position.z),



    float_word(s->velocity.x),float_word(s->velocity.y),float_word(s->velocity.z),float_word(s->speed),float_word(s->angle),



    float_word(s->hitbox.x),float_word(s->hitbox.y),u32(s->lifetime.current),u32(u16(s->sprite))|(u32(u16(s->color))<<16),s->active_transforms};



   reference_bullets.insert(reference_bullets.end(),std::begin(row),std::end(row));



  }



 }



 reference_items.clear();



 if(reference[30]==3&&reference[0]>=7075&&reference[0]<=7240){



  for(u32 n=0;n<ItemManager::capacity;++n){const auto& s=b.items.at(n);if(!s.state)continue;



   const u32 row[]={u32(s.state),u32(s.type),u32(s.display_type),float_word(s.position.x),float_word(s.position.y),float_word(s.position.z),



    float_word(s.velocity.x),float_word(s.velocity.y),float_word(s.velocity.z),float_word(s.lifetime.fractional),float_word(s.attraction_speed),u32(s.delay)};



   reference_items.insert(reference_items.end(),std::begin(row),std::end(row));



  }



 }



}



API(begin_reference) i32 begin_reference(u32 demo){



 if(!begin_demo(demo))return 0;reference_rng_reads.clear();session.battle->before_player_update=observe_reference;



 if(demo==1||demo==2)session.battle->enemy_environment.th14_random_read=observe_rng_read;return 1;



}



API(reference_data) const u32* reference_data(){return reference;}



API(reference_reward_data) const u32* reference_reward_data(){return reference_rewards;}



API(reference_rng_read_data) const u32* reference_rng_read_data(){return reference_rng_reads.data();}



API(reference_rng_read_words) u32 reference_rng_read_words(){return u32(reference_rng_reads.size());}



API(reference_shot_data) const u32* reference_shot_data(){return reference_shots.data();}



API(reference_shot_words) u32 reference_shot_words(){return u32(reference_shots.size());}



API(reference_enemy_data) const u32* reference_enemy_data(){return reference_enemies.data();}



API(reference_enemy_words) u32 reference_enemy_words(){return u32(reference_enemies.size());}



API(reference_phase_data) const u32* reference_phase_data(){return reference_phases.data();}



API(reference_phase_words) u32 reference_phase_words(){return u32(reference_phases.size());}



API(reference_item_data) const u32* reference_item_data(){return reference_items.data();}



API(reference_item_words) u32 reference_item_words(){return u32(reference_items.size());}



API(reference_bullet_data) const u32* reference_bullet_data(){return reference_bullets.data();}



API(reference_bullet_words) u32 reference_bullet_words(){return u32(reference_bullets.size());}



API(reference_beam_failure) const float* reference_beam_failure(){return session.battle->player->shots.th14_beam_failure.data();}







API(reference_area_data) const u32* reference_area_data(){return reference_areas.data();}



API(reference_area_words) u32 reference_area_words(){return u32(reference_areas.size());}







API(reference_id_data) const u32* reference_id_data(){return reference_ids.data();}



API(reference_id_words) u32 reference_id_words(){return u32(reference_ids.size());}



API(reference_next_id) u32 reference_next_id(){return reference_next_id_value;}



API(reference_popup_data) const u32* reference_popup_data(){return reference_popups.data();}



API(reference_popup_cursor) u32 reference_popup_cursor(){return reference_popup_cursor_value;}







API(begin_custom_reference) u32 begin_custom_reference(const u8* data,u32 size){



    if(!session.begin_replay(source,data,size,0,true))return 0;



    reference_rng_reads.clear();session.battle->before_player_update=observe_reference;return 1;



}







static u32 public_player_observations=0;



static u32 public_observed_stage_active=0;



API(public_replay_begin) u32 public_replay_begin(const u8* data,u32 size){



    session.interactive=false;



    if(!session.begin_replay(source,data,size,0,false))return 0;



    public_player_observations=0;



    public_observed_stage_active=0;



    session.battle->before_player_update=[](const GameBattle& battle){



        ++public_player_observations;public_observed_stage_active=battle.stage_active;observe_reference(battle);



    };



    return 1;



}



API(public_replay_clock) u32 public_replay_clock(double now){return session.sample_spell_clock(now);}



API(public_replay_observations) u32 public_replay_observations(){return public_player_observations;}



API(public_replay_observed_active) u32 public_replay_observed_active(){return public_observed_stage_active;}



API(public_replay_status) u32 public_replay_status(u32 field){



    const u32 values[]={session.state.stage,session.state.frame,session.battle?session.battle->frame:0,



        session.battle?u32(session.battle->game_over_requested):0,session.battle?u32(session.battle->stage_active):0,



        g_th14_bullet_unhandled,g_th14_bullet_unsupported_native};



    return field<7?values[field]:0;



}





#include "StageUploadsTh14.hpp"
#include "TextureImage.hpp"
#include "AnmGeometry.hpp"






static std::vector<u32> shot_animation_records;







API(shot_animation_data) const u32* shot_animation_data(){return shot_animation_records.data();}







API(shot_animation_words) u32 shot_animation_words(){return shot_animation_records.size();}







static void observe_shot_animations(const GameBattle& b){







 shot_animation_records.clear();







 if(b.resources.stage_number!=3||b.control_frame()<7075||b.control_frame()>7240)return;







 for(u32 n=0;n<256;++n){const auto& shot=b.player->shots.at(n);if(!shot.state)continue;







  const auto* root=b.animations.find(shot.animation);std::vector<const AnmVm*> nodes;







  for(auto* p=root;p;p=p->parent){if(nodes.size()>=16)std::abort();nodes.push_back(p);}







  Vec3 quad[4]{};const bool valid=root&&anm_quad_positions(*root,quad,b.animations.render_space);







  const u32 head[]={n,shot.animation,u32(nodes.size()),u32(valid)};







  shot_animation_records.insert(shot_animation_records.end(),std::begin(head),std::end(head));







  for(const auto& point:quad){shot_animation_records.push_back(float_word(point.x));shot_animation_records.push_back(float_word(point.y));shot_animation_records.push_back(float_word(point.z));}







  for(const auto* p:nodes){const auto& v=*p;







   const u32 words[]={v.flags2,v.drawing_mode(),(v.flags>>18)&3,(v.flags>>20)&3,







    float_word(v.position.x),float_word(v.position.y),float_word(v.position.z),







    float_word(v.script_position.x),float_word(v.script_position.y),float_word(v.script_position.z),







    float_word(v.child_position.x),float_word(v.child_position.y),float_word(v.child_position.z),







    float_word(v.rotation.x),float_word(v.rotation.y),float_word(v.rotation.z),







    float_word(v.scale.x),float_word(v.scale.y),float_word(v.extra_scale.x),float_word(v.extra_scale.y),







    float_word(v.sprite_size.x),float_word(v.sprite_size.y),float_word(v.pivot.x),float_word(v.pivot.y),







    u32(v.timer.previous),u32(v.timer.current),float_word(v.timer.fractional),







    u32(v.age.previous),u32(v.age.current),float_word(v.age.fractional),u32(v.parent!=nullptr)};







   static_assert(sizeof(words)==31*4);shot_animation_records.insert(shot_animation_records.end(),std::begin(words),std::end(words));







  }







 }







}



















static std::vector<u32> all_shot_records,all_shot_memory,all_shot_specs,window_meta;



API(all_shot_data) const u32* all_shot_data(){return all_shot_records.data();}



API(all_shot_words) u32 all_shot_words(){return all_shot_records.size();}



API(all_shot_memory_data) const u32* all_shot_memory_data(){return all_shot_memory.data();}



API(all_shot_memory_words) u32 all_shot_memory_words(){return all_shot_memory.size();}



API(all_shot_spec_data) const u32* all_shot_spec_data(){return all_shot_specs.data();}



API(all_shot_spec_words) u32 all_shot_spec_words(){return all_shot_specs.size();}



API(window_meta_data) const u32* window_meta_data(){return window_meta.data();}



API(window_meta_words) u32 window_meta_words(){return window_meta.size();}



static void observe_full_shots(const GameBattle& b){



 all_shot_records.clear();all_shot_memory.clear();all_shot_specs.clear();window_meta.clear();



 if(b.resources.stage_number!=3||b.control_frame()<7075||b.control_frame()>7240)return;



 const auto& space=b.animations.render_space;



 const u32 meta[]={u32(b.resources.stage_number),u32(b.control_frame()),b.frame,u32(b.stage_active),



   float_word(space.scale),float_word(space.play_origin.x),float_word(space.play_origin.y),float_word(space.scaled_origin.x),float_word(space.scaled_origin.y),



   sizeof(ShotState),sizeof(ShotSpec),49};window_meta.assign(std::begin(meta),std::end(meta));



 for(u32 n=0;n<256;++n){const auto& s=b.player->shots.at(n);



  const u32 row[]={n,u32(s.state),s.animation,s.extra_animation,u32(s.timer.previous),u32(s.timer.current),float_word(s.timer.fractional),u32(s.timer.rate!=nullptr),



   float_word(s.movement.position.x),float_word(s.movement.position.y),float_word(s.movement.position.z),float_word(s.movement.velocity.x),float_word(s.movement.velocity.y),float_word(s.movement.velocity.z),



   float_word(s.movement.speed),float_word(s.movement.angle),float_word(s.movement.radius),float_word(s.movement.radial_velocity),float_word(s.movement.ellipse_angle),float_word(s.movement.ellipse_ratio),s.movement.flags,



   u32(s.target!=nullptr),s.target?u32(s.target->state.instance_id):0,u32(s.hit_this_frame),u32(s.hit_last_frame),u32(s.damage),float_word(s.acceleration),u32(s.spec!=nullptr),



   u32(s.th14_steering.previous),u32(s.th14_steering.current),float_word(s.th14_steering.fractional),u32(s.th14_steering.rate!=nullptr),



   u32(s.th14_decay.previous),u32(s.th14_decay.current),float_word(s.th14_decay.fractional),u32(s.th14_decay.rate!=nullptr),



   s.th14_target_id,s.th14_area_flags,float_word(s.th14_area_radius),float_word(s.th14_area_growth),float_word(s.th14_saved_speed),s.th14_area_slot,s.th14_was_focused,s.th14_shot_flags,float_word(s.th14_beam_length),



   float_word(s.th14_attachment_offset.x),float_word(s.th14_attachment_offset.y),float_word(s.th14_attachment_offset.z),u32(s.th14_homing_target_retired)};



  static_assert(sizeof(row)==49*4);all_shot_records.insert(all_shot_records.end(),std::begin(row),std::end(row));



  u32 raw[sizeof(ShotState)/4];std::memcpy(raw,&s,sizeof(s));all_shot_memory.push_back(n);all_shot_memory.insert(all_shot_memory.end(),std::begin(raw),std::end(raw));



  u32 spec[sizeof(ShotSpec)/4]{};if(s.spec)std::memcpy(spec,s.spec,sizeof(spec));all_shot_specs.push_back(n);all_shot_specs.insert(all_shot_specs.end(),std::begin(spec),std::end(spec));



 }



}







static u64 probe_clock_ns=0;







static u32 probe_owner=0;







static std::vector<u32> knife_details;







API(knife_data) const u32* knife_data(){return knife_details.data();}







API(knife_words) u32 knife_words(){return knife_details.size();}















struct ProbeStageEffects final:StageResourceEffects {







 th11::sdl::StageUploadsTh14 queue;







 std::vector<u32> events;







 std::string error;







 bool prepare_stage_phase(StageResources& s,Phase p)override{return queue.begin(s,p);}







 bool stage_phase_ready(Phase p)const override{return queue.ready(p);}







 void finish_stage_phases(StageResources& s,u32)override{queue.finish(s);}







 void cancel_stage_phases(StageResources& s,u32)override{queue.cancel(s);}







 void release(StageResources& s)override{queue.cancel(s);}







 const std::string& last_error()const override{return error;}







 bool pump(){







  if(!queue.pending())return true;







  return queue.advance([&](const auto& job){







   TextureImage decoded;







   if(job.chunk>=job.resource->textures.size()||!decoded.load(job.resource->textures[job.chunk])){







    error="Real TextureImage conversion failed in declared no-upload queue probe";return false;







   }







   const u32 row[]={queue.owner()->stage_number,job.file,job.chunk,public_player_observations};







   events.insert(events.end(),std::begin(row),std::end(row));







   return true;







  });







 }







};







static ProbeStageEffects probe_effects;







static bool probe_async=false;







API(probe_clock_begin) void probe_clock_begin(){probe_clock_ns=0;session.stage_load_clock=[](){return probe_clock_ns;};}







API(probe_attach) void probe_attach(u32 async){







 probe_async=async!=0;session.resources.effects=probe_async?&probe_effects:nullptr;







 session.battle->before_player_update=[](const GameBattle& b){







  ++public_player_observations;public_observed_stage_active=b.stage_active;







  probe_owner=b.enemies.owner_present();observe_reference(b);observe_shot_animations(b);observe_full_shots(b);







  knife_details.clear();







  if(b.control_frame()>=2820&&b.control_frame()<=2900){







   const auto& p=b.player->shots.player;







   const u32 player[]={u32(p.th14_cached_power),u32(p.th14_attached_count),p.focused,u32(p.state),u32(p.th14_dialogue_blocked),u32(p.th14_enemy_manager)};







   knife_details.insert(knife_details.end(),std::begin(player),std::end(player));







   for(u32 n=0;n<256;++n){const auto& s=b.player->shots.at(n);if(!s.state)continue;







    const u32 row[]={n,s.th14_shot_flags,u32(s.timer.previous),u32(s.timer.current),float_word(s.timer.fractional),







      u32(s.th14_steering.previous),u32(s.th14_steering.current),float_word(s.th14_steering.fractional),







      u32(s.th14_decay.previous),u32(s.th14_decay.current),float_word(s.th14_decay.fractional),







      s.th14_target_id,u32(s.target!=nullptr),u32(s.target?s.target->state.th14_attached_knives:0),







      u32(s.th14_homing_target_retired),s.th14_area_slot,







      float_word(s.th14_attachment_offset.x),float_word(s.th14_attachment_offset.y),float_word(s.th14_attachment_offset.z),







      s.spec?s.spec->native_tail[1]:0,s.spec?s.spec->native_tail[3]:0,u32(s.damage)};







    knife_details.insert(knife_details.end(),std::begin(row),std::end(row));







   }







  }















 };







}







API(probe_tick) u32 probe_tick(u64 now){







 probe_clock_ns=now;







 if(probe_async&&!probe_effects.pump())return 0;







 return session.update({0});







}







API(probe_retire_capture) void probe_retire_capture(){session.animations.retire_deferred_captures_without_target();}







API(probe_owner_present) u32 probe_owner_present(){return probe_owner;}







API(probe_queue_data) const u32* probe_queue_data(){return probe_effects.events.data();}







API(probe_queue_words) u32 probe_queue_words(){return probe_effects.events.size();}







API(probe_error) const char* probe_error(){return probe_effects.error.c_str();}











API(selected_player_name) const char* selected_player_name(){return player_file_name(u32(session.state.character),u32(session.state.subtype));}

API(selected_player_body_file) u32 selected_player_body_file(){return session.battle&&session.battle->player?session.battle->player->motion.body.file_index:0;}

API(selected_player_scripts) u32 selected_player_scripts(){return session.resources.core.players[session.state.character].scripts.size();}

API(selected_player_script_id) i32 selected_player_script_id(u32 i){const auto& f=session.resources.core.players[session.state.character];return i<f.scripts.size()?f.scripts[i].source_id:0x7fffffff;}

API(selected_player_script) const u8* selected_player_script(u32 i){const auto& f=session.resources.core.players[session.state.character];return i<f.scripts.size()?f.scripts[i].bytes.data():nullptr;}

API(selected_player_script_size) u32 selected_player_script_size(u32 i){const auto& f=session.resources.core.players[session.state.character];return i<f.scripts.size()?f.scripts[i].bytes.size():0;}

API(selected_player_portrait) const u8* selected_player_portrait(){const auto& f=session.resources.core.players[session.state.character];return f.textures.back().pixels.data();}

API(selected_player_portrait_size) u32 selected_player_portrait_size(){const auto& f=session.resources.core.players[session.state.character];return f.textures.back().pixels.size();}



API(menu_interactive) void menu_interactive(u32 enabled){session.interactive=enabled!=0;}

API(menu_tick) u32 menu_tick(u64 now,u32 held){probe_clock_ns=now;if(probe_async&&!probe_effects.pump())return 0;return session.update({held});}

API(menu_state) u32 menu_state(u32 field){const auto* m=session.pause_menu.get();const auto* b=session.battle.get();const u32 v[]={

 u32(session.state.phase),session.state.stage,session.state.frame,public_player_observations,

 u32(m!=nullptr),m?u32(m->state):0xffffffffu,m?u32(m->replay):0,m?u32(m->forced_exit):0,m?u32(m->sounds.size()):0,

 b?u32(b->game_over_requested):0,b?u32(b->completion.state.exit):0,

 u32(session.economy.score_units),u32(session.economy.lives),b?u32(b->player->state.life_state):0,

 b?u32(b->control_frame()):0,float_bits(session.animations.rate),m?u32(m->cursor.selected):0,m?u32(m->cursor.count):0,

 m?u32(m->cursor.disabled_count):0,m?u32(m->action):0};return field<20?v[field]:0;

}

API(menu_disabled) u32 menu_disabled(u32 n){const auto* m=session.pause_menu.get();return m&&n<u32(m->cursor.disabled_count)?u32(m->cursor.disabled[n]):0xffffffffu;}



#include <new>



// Source-bound diagnostic adapter for Application.cpp's real boot queue.

// A texture chunk is treated as successfully uploaded without a GPU. It does

// not claim to reproduce original worker scheduling or GPU completion times.

struct ColdEntryEffects final:StageResourceEffects {

    struct Job {AnmResource* resource;u16 file;u32 chunk=0;};

    std::vector<Job> jobs;

    u32 index=0,sig_draws=0,sig_handle=0;

    bool done=false,sig_active=false,sig_pending=false,sig_uploaded=false,ascii_pending=false,ascii_uploaded=false;

    u64 queued_ns[26]{},signature_flag_ns=0,ascii_flag_ns=0,title_ready_ns=0,initial_worker_ready_ns=0;

    bool stage_pending=false;

    AnmResource sig;

    LoadingTh14 loading;

    bool core_ready()const override{return done;}

    bool stage_ready()const override{return index==jobs.size()&&(!stage_pending||probe_clock_ns>=initial_worker_ready_ns);}

    bool prepare(StageResources& stage)override{

        jobs={{&session.resources.core.players[session.state.character],9},{&stage.background,u16((stage.stage_number&1)+3)},{&stage.logo,6}};index=0;

        for(u32 i=0;i<stage.ecl_animations.size();++i)if(!stage.ecl_animation_names[i].empty())jobs.push_back({&stage.ecl_animations[i],u16(10+i)});

        stage_pending=true;return true; // Controlled hypothesis: no second loading family at first entry.

    }

    bool draw_startup_loading()override{

        if(!sig_active||!sig_uploaded||probe_clock_ns<signature_flag_ns)return true;

        if(sig_pending){auto* vm=session.animations.create(sig,0,1,0xffffffffu);if(!vm)return false;sig_handle=vm->id;sig_pending=false;}

        if(ascii_uploaded&&ascii_pending&&probe_clock_ns>=ascii_flag_ns){if(!loading.begin(session.animations,session.resources.core.ascii))return false;ascii_pending=false;}

        ++sig_draws;return true;

    }

    bool begin(){

        if(!source.open_anm("sig.anm",sig)||!session.animations.prepare_resource(sig,1))return false;

        session.resources.effects=this;

        if(!session.open_title(source,true))return false;

        auto& c=session.resources.core;

        sig_active=sig_pending=ascii_pending=true;

        jobs={{&sig,1},{&c.ascii,2},{&c.text,0},{&c.front,5},{&c.bullet,7},{&c.effect,8},{&c.title,16},{&c.title_variant,17}};

        return true;

    }

    bool tick(u64 now){

        probe_clock_ns=now;

        if(index<jobs.size()||sig_active||stage_pending){

            if(index<jobs.size()&&probe_clock_ns>=queued_ns[jobs[index].file]){

                auto& j=jobs[index];

                if(!done&&index>=3){constexpr u32 ids[]={0,1,2,4,5};if(!session.resources.load_core_job(ids[index-3]))return false;}

                if(++j.chunk>=j.resource->textures.size()){

                    if(!session.animations.prepare_resource(*j.resource,j.file))return false;

                    if(j.resource==&sig)sig_uploaded=true;

                    if(j.resource==&session.resources.core.ascii)ascii_uploaded=true;

                    if(!done&&j.resource==&session.resources.core.text){if(!session.compositor.initialize(*j.resource))return false;session.compositor.reset_cameras(false);}

                    ++index;

                }

            }

            const bool ready=sig_active&&!sig_pending&&sig_draws>=180&&index==jobs.size()&&probe_clock_ns>=title_ready_ns;

            bool title_advanced=false;

            if(ready){

                session.animations.retire_resource(sig);done=true;

                if(session.state.phase==GameSessionPhase::loading&&!session.finish_loading())return false;

                if(session.state.phase==GameSessionPhase::title){

                    loading.finish(session.animations);

                    if(!session.update({}))return false;title_advanced=true;

                }

            }

            bool stage_advanced=false;

            if(stage_pending&&index==jobs.size()&&probe_clock_ns>=initial_worker_ready_ns){

                stage_pending=false;loading.finish(session.animations);jobs.clear();index=0;

                if(!session.finish_loading()||!session.update({}))return false;

                stage_advanced=true;

            }

            if(!title_advanced&&!stage_advanced&&(!session.animations.update(true)||!session.animations.update(false)))return false;

            if(ready){if(session.animations.references(sig))return false;renderer.invalidate();sig={};sig_active=false;sig_handle=0;}

            if(!stage_advanced&&!stage_pending&&index==jobs.size()&&!sig_active){

                done=true;loading.finish(session.animations);jobs.clear();index=0;

                if(session.state.phase==GameSessionPhase::loading&&!session.finish_loading())return false;

            }

            return draw();

        }

        return session.update({})&&draw();

    }

};

static ColdEntryEffects cold;

API(cold_begin) u32 cold_begin(u32 ticks){

    session.~GameSession();new(&session)GameSession(ticks);session.interactive=true;

    probe_clock_ns=0;session.stage_load_clock=[](){return probe_clock_ns;};

    return cold.begin();

}

API(cold_tick) u32 cold_tick(u64 now){return cold.tick(now);}

API(cold_state) u32 cold_state(u32 n){

    u32 serial=0,min_slot=8191;const u32 count=anm_creation_count(),first=count>4096?count-4096:0;

    for(u32 i=first;i<count;++i){const u32 id=u32(anm_creation_value(i,5));serial=std::max(serial,id>>13);min_slot=std::min(min_slot,id&8191u);}

    const u32 v[]={u32(session.state.phase),session.battle?1u:0u,serial,session.animations.script_rng.seed,session.animations.script_rng.calls,

        session.animations.visual_rng.seed,session.animations.visual_rng.calls,u32(session.state.demo),cold.sig_draws,cold.index,u32(cold.jobs.size()),session.animations.active_count(),

        min_slot,u32(session.state.character),u32(session.state.subtype),u32(session.state.difficulty)};

    return n<16?v[n]:0;

}

API(cold_attach_warm_case) u32 cold_attach_warm_case(){

    if(!session.battle||session.state.phase!=GameSessionPhase::stage||!session.state.demo)return 0;

    // The same declared attract-mode clear as the Native warm case; this

    // does not initialize RNG, health, input, counters or ANM serial numbers.

    session.state.demo=false;session.battle->demo=false;

    public_player_observations=0;

    session.battle->before_player_update=[](const GameBattle& b){++public_player_observations;public_observed_stage_active=b.stage_active;capture_mid_live();observe_reference(b);};

    probe_attach(1);return 1;

}



API(cold_creation_count) u32 cold_creation_count(){return anm_creation_count();}

API(cold_creation_value) i32 cold_creation_value(u32 n,u32 f){return anm_creation_value(n,f);}



API(cold_live_value) u32 cold_live_value(u32 id,u32 n){

 const auto* vm=session.animations.find(id);if(!vm)return 0xffffffffu;

 const u32 fields[]={vm->id,u32(vm->file_index),u32(vm->script_index),u32(vm->timer.previous),u32(vm->timer.current),float_bits(vm->timer.fractional),vm->flags,vm->flags2,u32(vm->pending_interrupt),u32(vm->age.current)};

 return n<10?fields[n]:0;

}



API(reference_environment) u32 reference_environment(u32 cookie,u32 frame){

 if(cold.sig_draws||session.battle||!NativeStackTh14::preinitialized_cookie(cookie)||(frame&3u))return 0;

 session.animations.th14_native_stack.configure(cookie,frame);return 1;

}



API(cold_host_queue) u32 cold_host_queue(u32 file,u64 ready){

 if(file>=26||cold.sig_draws||session.battle)return 0;

 cold.queued_ns[file]=ready;return 1;

}

API(cold_host_flags) u32 cold_host_flags(u64 sig,u64 ascii){

 if(cold.sig_draws||session.battle||ascii<sig)return 0;

 cold.signature_flag_ns=sig;cold.ascii_flag_ns=ascii;return 1;

}



API(cold_host_title_ready) u32 cold_host_title_ready(u64 ready){

 if(cold.sig_draws||session.battle)return 0;

 cold.title_ready_ns=ready;return 1;

}



API(cold_host_initial_worker_ready) u32 cold_host_initial_worker_ready(u64 ready){

 if(cold.sig_draws||session.battle)return 0;

 cold.initial_worker_ready_ns=ready;return 1;

}

static bool warm_at_first_player=false;

API(cold_host_warm_at_first_player) u32 cold_host_warm_at_first_player(){if(session.battle)return 0;warm_at_first_player=true;return 1;}

API(cold_host_initial_player) u32 cold_host_initial_player(u64 now){

 probe_clock_ns=now;

 if(!cold.stage_pending||!cold.index||cold.jobs[0].file!=9)return 0;

 if(!session.prepare_initial_player())return 0;

 session.battle->before_player_update=[](const GameBattle& b){if(warm_at_first_player){session.state.demo=false;session.battle->demo=false;warm_at_first_player=false;}++public_player_observations;capture_mid_live();observe_reference(b);};

 return 1;

}



API(cold_host_signature_retire) u32 cold_host_signature_retire(u64 now){

 probe_clock_ns=now;

 if(!cold.sig_active)return 0;

 session.animations.retire_resource(cold.sig);return 1;

}



static std::vector<u32> expanded_live_fields(const AnmVm& v){std::vector<u32> out={v.sprite?u32(v.sprite_index):u32(-1),v.flags&1,v.drawing_mode(),v.color,v.secondary_color,v.layer,v.flags2,u32(v.timer.previous),u32(v.timer.current),float_bits(v.timer.fractional),u32(v.age.previous),u32(v.age.current),float_bits(v.age.fractional)};

 for(const float x:{v.script_position.x,v.script_position.y,v.script_position.z,v.rotation.x,v.rotation.y,v.rotation.z,v.angular_velocity.x,v.angular_velocity.y,v.angular_velocity.z,v.scale.x,v.scale.y,v.extra_scale.x,v.extra_scale.y,v.texture_scale.x,v.texture_scale.y,v.uv_offset.x,v.uv_offset.y,v.scroll_velocity.x,v.scroll_velocity.y,v.sprite_size.x,v.sprite_size.y})out.push_back(float_bits(x));

 for(const auto& uv:v.uv){out.push_back(float_bits(uv.x));out.push_back(float_bits(uv.y));}for(i32 i:v.integers)out.push_back(u32(i));for(float x:v.floats)out.push_back(float_bits(x));out.push_back(v.instruction?u32(reinterpret_cast<const u8*>(v.instruction)-reinterpret_cast<const u8*>(v.script_begin)):u32(-1));return out;}



template<class T,u32 N> static void append_interpolator(std::vector<u32>& out,const Interpolator<T,N>& v){

 for(const auto* a:{v.start,v.end,v.initial_tangent,v.final_tangent})for(u32 n=0;n<N;++n){u32 word;std::memcpy(&word,a+n,4);out.push_back(word);}

 for(u32 x:{u32(v.timer.previous),u32(v.timer.current),float_bits(v.timer.fractional),v.timer.flags,u32(v.duration),u32(v.mode)})out.push_back(x);

}



static std::vector<std::vector<u32>> mid_rows[32];

static u32 mid_expected_rows[32]{};

static u32 mid_frames[32]={1,26000,30000,36000,38900,60000,90000,120000};

static void capture_mid_live(){

 capture_combat_checkpoint();

 const auto& c=session.compositor.world_camera;u32 k=0;

 for(float x:{c.position.x,c.position.y,c.position.z,c.direction.x,c.direction.y,c.direction.z,c.up.x,c.up.y,c.up.z,c.reserved24.x,c.reserved24.y,c.reserved24.z,c.right.x,c.right.y,c.right.z,c.eye_offset.x,c.eye_offset.y,c.eye_offset.z,c.target_offset.x,c.target_offset.y,c.target_offset.z,c.fov,c.animation_delta.x,c.animation_delta.y,c.animation_delta.z})camera_words[k++]=float_bits(x);

 camera_creation_count=anm_creation_count();

 hud_words[0]=session.battle?u32(session.battle->hud.score.displayed):0xffffffffu;hud_words[1]=u32(session.economy.score_units);



 u32 at=32;for(u32 i=0;i<32;++i)if(mid_frames[i]&&public_player_observations==mid_frames[i])at=i;if(at==32||!mid_rows[at].empty())return;

 auto& manager=session.animations;auto& rows=mid_rows[at];mid_expected_rows[at]=manager.active_count();

 std::vector<u32> seen;

 for(u32 layer=0;layer<36;++layer){auto* seed=manager.layer_first(layer);if(!seed)continue;

  auto* node=&seed->registry;u32 back=0;while(node->previous){node=node->previous;if(++back>8192)return;}

  for(u32 budget=0;node&&budget<8192;node=node->next,++budget){

   const auto* vm=node->value;if(!vm||manager.find(vm->id)!=vm)return;

   bool duplicate=false;for(u32 id:seen)if(id==vm->id)duplicate=true;if(duplicate)continue;seen.push_back(vm->id);

   std::vector<u32> row={vm->id,u32(vm->file_index),u32(vm->script_index),u32(vm->timer.previous),u32(vm->timer.current),float_bits(vm->timer.fractional),u32(vm->pending_interrupt),u32(vm->age.current)};

   const auto extra=expanded_live_fields(*vm);row.insert(row.end(),extra.begin()+1,extra.end());for(float x:{vm->position.x,vm->position.y,vm->position.z})row.push_back(float_bits(x));row.push_back((vm->th13_native_flags>>17)&3u); for(u32 x:{vm->blend_mode(),u32((vm->flags&0x800)!=0),u32((vm->flags&0x200)!=0),u32((vm->flags&0x400)!=0),(vm->flags>>18)&3u,(vm->flags>>20)&3u,vm->th13_native_flags>>30,u32((vm->th13_native_flags&0x8000)!=0)})row.push_back(x); for(float x:{vm->extra_floats.x,vm->extra_floats.y,vm->extra_floats.z})row.push_back(float_bits(x));for(i32 x:vm->extra_integers)row.push_back(u32(x));for(float x:{vm->random_scale.x,vm->random_scale.y})row.push_back(float_bits(x));row.push_back(u32(vm->random_bound));row.push_back(float_bits(vm->scale_velocity.x));row.push_back(float_bits(vm->scale_velocity.y));append_interpolator(row,vm->position_interpolation);append_interpolator(row,vm->color_interpolation);append_interpolator(row,vm->alpha_interpolation);append_interpolator(row,vm->rotation_interpolation);append_interpolator(row,vm->scale_interpolation);append_interpolator(row,vm->color2_interpolation);append_interpolator(row,vm->alpha2_interpolation);append_interpolator(row,vm->scroll_x_interpolation);append_interpolator(row,vm->scroll_y_interpolation);append_interpolator(row,vm->extra_scale_interpolation);append_interpolator(row,vm->texture_scale_interpolation);for(float x:{vm->child_position.x,vm->child_position.y,vm->child_position.z,vm->pivot.x,vm->pivot.y,vm->slowdown_factor})row.push_back(float_bits(x));

row.push_back(vm->parent?vm->parent->id:0);row.push_back(vm->timer.flags);row.push_back(vm->age.flags);

for(const Matrix4* m:{&vm->sprite_matrix,&vm->transform_matrix,&vm->uv_matrix})for(float x:m->m)row.push_back(float_bits(x));

for(const auto* n:{vm->registry.next,vm->registry.previous,vm->child.next,vm->child.previous})row.push_back(n?n->value->id:0);

for(u32 x:{u32(vm->saved_timer.previous),u32(vm->saved_timer.current),float_bits(vm->saved_timer.fractional),u32(vm->saved_timer.rate!=nullptr),vm->saved_timer.flags,vm->saved_instruction?u32(uintptr_t(vm->saved_instruction)-uintptr_t(vm->script_begin)):0xffffffffu,u32(vm->sprite_frame),vm->inherited_color})row.push_back(x);

rows.push_back(std::move(row));

  }

 }

}

API(observation_snapshot_target) u32 observation_snapshot_target(u32 at,u32 callback){if(public_player_observations||at>=32)return 0;mid_frames[at]=callback;return 1;}
API(mid_count) u32 mid_count(u32 at){return at<32?u32(mid_rows[at].size()):0;}

API(mid_complete) u32 mid_complete(u32 at){return at<32&&mid_rows[at].size()==mid_expected_rows[at];}

API(mid_expected) u32 mid_expected_count(u32 at){return at<32?mid_expected_rows[at]:0;}

API(mid_value) u32 mid_value(u32 at,u32 row,u32 field){return at<32&&row<mid_rows[at].size()&&field<303?mid_rows[at][row][field]:0xffffffffu;}



struct ObservedWorkerEffects final:StageResourceEffects {

    StageResourceEffects* next=nullptr;

    u64 ready_ns[8]{},initialize_ns[8]{},phase_ready_ns[8][3]{};u32 begins=0;

    bool prepare(StageResources& s)override{return next->prepare(s);}

    bool core_ready()const override{return next->core_ready();}

    bool stage_ready()const override{return next->stage_ready();}

    bool begin_stage_worker_wait(bool initial)override{++begins;return next->begin_stage_worker_wait(initial);}

    bool stage_worker_wait_ready()const override{return (session.state.stage<8&&probe_clock_ns>=ready_ns[session.state.stage]&&probe_clock_ns>=initialize_ns[session.state.stage])&&next->stage_worker_wait_ready();}

    bool draw_startup_loading()override{return next->draw_startup_loading();}

    bool defer_ending_loading()const override{return next->defer_ending_loading();}

    bool begin_ending_loading()override{return next->begin_ending_loading();}

    void finish_ending_loading()override{next->finish_ending_loading();}

    DialogueEffects* dialogue_text_device()override{return next->dialogue_text_device();}

    void release(StageResources& s)override{next->release(s);}

    bool prepare_animation(AnmResource& a)override{return next->prepare_animation(a);}

    bool prepare_manual_image(AnmResource& a,u32 i,const u8* p,u32 n)override{return next->prepare_manual_image(a,i,p,n);}

    void release_animation(AnmResource& a)override{next->release_animation(a);}

    bool read_replay(const std::string& p,std::vector<u8>& b)override{return next->read_replay(p,b);}

    const std::string& last_error()const override{return next->last_error();}

    bool prepare_stage_phase(StageResources& s,Phase p)override{return next->prepare_stage_phase(s,p);}

    bool stage_phase_ready(Phase p)const override{return session.state.stage<8&&probe_clock_ns>=phase_ready_ns[session.state.stage][u32(p)]&&next->stage_phase_ready(p);}

    void cancel_stage_phases(StageResources& s,u32 n)override{next->cancel_stage_phases(s,n);}

    void finish_stage_phases(StageResources& s,u32 n)override{next->finish_stage_phases(s,n);}

};

static ObservedWorkerEffects observed_worker_effects;
API(observed_worker_initialize) u32 observed_worker_initialize(u32 stage,u64 now){
    if(!observed_worker_effects.next||stage<2||stage>6||now<observed_worker_effects.ready_ns[stage])return 0;
    observed_worker_effects.initialize_ns[stage]=now;return 1;
}

// Optional scheduler observations belong to the test host. They advance real
// loader actions at callback boundaries and never replace gameplay values.
static u64 observed_player_boundary_ns=0;
static bool observed_player_boundary_pending=false,observed_boundary_failed=false;
static bool service_observed_worker(u64 now){
    if(now<probe_clock_ns)return false;
    probe_clock_ns=now;
    return !session.battle||!session.battle->pending_stage||
        session.battle->pump_stage_loading(now,session.animations.first_deferred_capture_file_index(),session.stage_load_host_flags);
}
API(observed_player_boundary) u32 observed_player_boundary(u32 callback,u64 now){
    if(observed_player_boundary_pending||callback!=public_player_observations+1||now<probe_clock_ns)return 0;
    observed_player_boundary_ns=now;observed_player_boundary_pending=true;return 1;
}
API(observed_worker_boundary) u32 observed_worker_boundary(u64 now){return service_observed_worker(now);}
API(observed_boundary_ok) u32 observed_boundary_ok(){return !observed_boundary_failed&&!observed_player_boundary_pending;}

API(observed_worker_events) u32 observed_worker_events(u32 stage,u64 start,u64 ready){

    if(public_player_observations!=1||session.state.stage!=1||stage<2||stage>6||!session.resources.effects||ready<start||ready-start<60000000)return 0;

    if(!observed_worker_effects.next){probe_attach(1);static auto observed_player_callback=session.battle->before_player_update;session.battle->before_player_update=[](const GameBattle& b){if(observed_player_boundary_pending){observed_player_boundary_pending=false;if(!service_observed_worker(observed_player_boundary_ns)){observed_boundary_failed=true;return;}}observed_player_callback(b);capture_mid_live();};observed_worker_effects.next=session.resources.effects;session.resources.effects=&observed_worker_effects;}

    observed_worker_effects.ready_ns[stage]=ready;return 1;

}

API(observed_worker_begins) u32 observed_worker_begins(){return observed_worker_effects.begins;}



API(observed_phase_events) u32 observed_phase_events(u32 stage,u64 hud,u64 scene,u64 timeline){

 if(!observed_worker_effects.next||stage<2||stage>6||scene<hud||timeline<scene)return 0;

 auto* v=observed_worker_effects.phase_ready_ns[stage];v[0]=hud;v[1]=scene;v[2]=timeline;return 1;

}



API(observed_camera_word) u32 observed_camera_word(u32 field){return field<25?camera_words[field]:0xffffffffu;}

API(observed_creation_count) u32 observed_creation_count(){return camera_creation_count;}



API(observed_hud_word) u32 observed_hud_word(u32 n){return n<2?hud_words[n]:0xffffffffu;}

API(current_hud_word) u32 current_hud_word(u32 n){return n==0?(session.battle?u32(session.battle->hud.score.displayed):0xffffffffu):n==1?u32(session.economy.score_units):0xffffffffu;}



API(cold_host_ascii_draw_begin) u32 cold_host_ascii_draw_begin(u64 now){

 if(session.battle||!cold.sig_active||!cold.ascii_uploaded)return 0;

 if(!cold.ascii_pending)return cold.loading.handle?2u:0u;

 probe_clock_ns=now;

 if(!cold.loading.begin(session.animations,session.resources.core.ascii))return 0;

 cold.ascii_pending=false;return 1;

}



// Observer-only semantic serialization at the same before-Player boundary.

// Every active object is retained, with original linked-list or pool order.

static u32 combat_callback=0,combat_stage=0,combat_frame=0;

static std::vector<u32> combat_rows[6];

static void capture_combat_checkpoint(){

 if(!session.battle||!session.battle->player)return;

 const auto& b=*session.battle;const u32 callback=public_player_observations,frame=u32(b.control_frame());

 if(combat_callback==callback)return;

 const bool due=callback==1||callback%997==0||callback==26000||callback==30000||callback==36000||callback==38900||callback==60000||callback==90000||callback==120000||frame==0||frame==1||frame==900||frame==3000||frame==4500||frame==4577;

 if(!due)return;

 combat_callback=callback;combat_stage=session.state.stage;combat_frame=frame;

 for(auto& row:combat_rows)row.clear();

 auto& enemies=combat_rows[0];

 for(auto* n=b.enemies.first;n;n=n->next){const auto& e=n->value->state;

  for(u32 x:{u32(e.instance_id),u32(e.health),u32(e.max_health),u32(e.score),e.flags})enemies.push_back(x);

  for(const auto* m:{&e.current,&e.absolute,&e.relative})for(float x:{m->position.x,m->position.y,m->position.z,m->velocity.x,m->velocity.y,m->velocity.z})enemies.push_back(float_bits(x));

  for(const auto* m:{&e.current,&e.absolute,&e.relative})for(float x:{m->speed,m->angle})enemies.push_back(float_bits(x));

  enemies.push_back(u32(e.damage_immunity.current));enemies.push_back(u32(e.timer_2bc.current));

 }

 auto& bullets=combat_rows[1];

 for(auto* s=b.bullets.first_th14();s;s=s->th14_active_next){

  for(u32 x:{u32(u16(s->state)),s->flags,u32(s->collision_delay)})bullets.push_back(x);

  for(float x:{s->position.x,s->position.y,s->position.z,s->velocity.x,s->velocity.y,s->velocity.z,s->speed,s->angle,s->hitbox.x,s->hitbox.y})bullets.push_back(float_bits(x));

  for(u32 x:{u32(s->lifetime.current),u32(u16(s->sprite))|(u32(u16(s->color))<<16),s->active_transforms,float_bits(s->th14_size_current),float_bits(s->th14_size)})bullets.push_back(x);

 }

 auto& shots=combat_rows[2];auto& areas=combat_rows[3];const auto& manager=b.player->shots;

 for(u32 i=0;i<256;++i){const auto& s=manager.at(i);if(s.state){

  for(u32 x:{i,u32(s.state),u32(s.timer.previous),u32(s.timer.current),float_bits(s.timer.fractional),s.th14_shot_flags,s.animation})shots.push_back(x);

  // Retail shot +b0 retains its own beam length after retirement. Its damage-area
  // slot can already belong to another shot, so area.size.x is a different field.
  for(float x:{s.movement.position.x,s.movement.position.y,s.movement.position.z,s.movement.speed,s.movement.angle,s.movement.velocity.x,s.movement.velocity.y,s.movement.velocity.z,(s.spec&&s.spec->type==3?s.th14_beam_length:(s.spec?s.spec->hitbox.x:0.f))})shots.push_back(float_bits(x));

  for(u32 x:{u32(s.damage),u32(s.hit_this_frame),u32(s.hit_last_frame)})shots.push_back(x);

 }

 const auto* a=manager.th14_bomb_area(i);if(a&&(a->flags&1)){

  areas.push_back(i);areas.push_back(a->flags);

  for(float x:{a->radius,a->angle,a->size.x,a->size.y,a->position.x,a->position.y,a->position.z})areas.push_back(float_bits(x));

  for(u32 x:{u32(a->timer.previous),u32(a->timer.current),float_bits(a->timer.fractional),float_bits(a->growth),float_bits(a->angular_velocity),u32(a->damage),u32(a->total),u32(a->maximum),u32(a->period),a->stamp})areas.push_back(x);

 }}

 auto& lasers=combat_rows[5];

 for(auto* b0=b.lasers.first();b0;b0=b0->next){const auto& s=*b0;

  for(u32 x:{u32(s.id),u32(s.type),u32(s.state),u32(s.lifetime.previous),u32(s.lifetime.current),float_bits(s.lifetime.fractional),u32(s.graze_timer.previous),u32(s.graze_timer.current),float_bits(s.graze_timer.fractional)})lasers.push_back(x);

  for(float x:{s.position.x,s.position.y,s.position.z,s.velocity.x,s.velocity.y,s.velocity.z,s.angle,s.length,s.type==3?reinterpret_cast<const Th14LaserShell*>(b0)->native_scalar_74:s.width,s.speed,s.offset})lasers.push_back(float_bits(x));

  for(u32 x:{u32(s.type==2?reinterpret_cast<const Th14LaserCurve*>(b0)->path.transform_index:s.transform_index),s.active_transforms,u32(s.offscreen_timer.previous),u32(s.offscreen_timer.current),float_bits(s.offscreen_timer.fractional),u32(s.protection)})lasers.push_back(x);

 }

 auto& items=combat_rows[4];

 for(u32 i=0;i<ItemManager::capacity;++i){const auto& s=b.items.at(i);if(!s.state)continue;

  for(u32 x:{i,u32(s.state),u32(s.type),u32(s.display_type)})items.push_back(x);

  for(float x:{s.position.x,s.position.y,s.position.z,s.velocity.x,s.velocity.y,s.velocity.z,s.lifetime.fractional,s.attraction_speed})items.push_back(float_bits(x));items.push_back(u32(s.delay));

 }

}

API(combat_meta) u32 combat_meta(u32 n){const u32 words[]={combat_callback,combat_stage,combat_frame};return n<3?words[n]:0xffffffffu;}

API(combat_size) u32 combat_size(u32 family){return family<6?combat_rows[family].size():0;}

API(combat_data) const u32* combat_data(u32 family){return family<6?combat_rows[family].data():nullptr;}

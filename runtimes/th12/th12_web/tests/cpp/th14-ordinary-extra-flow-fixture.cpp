#include "StageCppWorkerTh14.hpp"
#define __EMSCRIPTEN__ 1
#include "Application.cpp"
#include "AnmGeometry.hpp"
#include "Th14WarmAttractCase.hpp"
#include <atomic>
extern "C" __attribute__((import_module("observerhost"),import_name("now_ns"))) th11::u64 th14_observer_now_ns();
namespace {
std::atomic<th11::u32> observer_published_callback{0},observer_rng_events{0};
std::array<th11::u32,256*16> observer_rng_rows{};
std::array<th11::u32,300000*8> observer_main_rows{};
th11::u64 observer_main_started=0;
std::array<th11::u32,24> observer_codec_warm_rows{};
std::vector<th11::u8> observer_live_score_snapshot;
th11::u32 observer_codec_warm_count=0;

touhou::sdl::FrameCadence observer_frame_cadence;
th11::u32 observer_frame_opportunities=0,observer_outer_ticks=0;
std::vector<th11::u32> observer_frame_rows;

}
using namespace th11;using namespace th11::sdl;
#define API(name) extern "C" __attribute__((export_name(#name)))
namespace {
std::unique_ptr<Application> current;GameSession* game=nullptr;
u32 menu_input_held=0;bool menu_pause_pending=false;
u32 callbacks=0;constexpr u32 stride=114;std::vector<u32> rows;
i32 keepalive=0;u32 pushes=0,pops=0;
namespace shot_lifetime_observer {
constexpr u32 stride=96;
static bool enabled=false;
u32 float_bits(float f){u32 w;std::memcpy(&w,&f,4);return w;}
static u32 callback=0,stage=0,frame=0,captures=0;
static std::vector<u32> words;

bool wanted(u32 cb,u32 s,u32 f){return cb==1||(s==1&&((f>=300&&f<=320)||(f>=1000&&f<=1040)));}
void capture(const GameBattle& battle,u32 cb){
 const u32 s=u32(battle.resources.stage_number),f=u32(battle.control_frame());
 if(!enabled||!battle.player||!wanted(cb,s,f))return;
 if(captures>=80)return;
 callback=cb;stage=s;frame=f;++captures;
 words.insert(words.end(),{cb,s,f,stride});
 const auto& space=battle.animations.render_space;
 for(u32 slot=0;slot<256;++slot){
  const auto& shot=battle.player->shots.at(slot);u32 row[stride]{};
  row[0]=slot;row[1]=u32(shot.state);row[2]=shot.animation;row[3]=shot.extra_animation;
  row[4]=u32(shot.timer.previous);row[5]=u32(shot.timer.current);row[6]=float_bits(shot.timer.fractional);
  row[7]=shot.th14_shot_flags;row[8]=shot.th14_area_slot;row[9]=u32(shot.damage);
  row[10]=u32(shot.hit_last_frame);row[11]=u32(shot.hit_this_frame);
  const float motion[]={shot.movement.position.x,shot.movement.position.y,shot.movement.position.z,
   shot.movement.velocity.x,shot.movement.velocity.y,shot.movement.speed,shot.movement.angle};
  for(u32 i=0;i<7;++i)row[12+i]=float_bits(motion[i]);
  // Inactive slots can retain stale specification pointers. Never dereference them.
  if(shot.state&&shot.spec){
   const auto& spec=*shot.spec;row[19]=spec.type;row[20]=spec.option;row[21]=u32(spec.spawn);
   row[22]=u32(spec.update);row[23]=spec.extra_callback;row[24]=u32(spec.animation);
   if(const auto* vm=battle.animations.find(shot.animation)){
    row[25]=1;row[26]=vm->id;row[27]=vm->file_index;row[28]=u32(vm->script_index);
    row[29]=vm->flags;row[30]=vm->flags2;row[31]=u32(vm->pending_interrupt);
    row[32]=u32(vm->timer.previous);row[33]=u32(vm->timer.current);row[34]=float_bits(vm->timer.fractional);
    row[35]=u32(vm->age.current);row[36]=vm->parent?vm->parent->id:0;row[37]=u32(vm->sprite_index);
    row[38]=vm->drawing_mode();row[39]=vm->instruction&&vm->script_begin?u32(uintptr_t(vm->instruction)-uintptr_t(vm->script_begin)):~0u;
    const float geometry[]={vm->position.x,vm->position.y,vm->position.z,vm->script_position.x,vm->script_position.y,vm->script_position.z,
     vm->child_position.x,vm->child_position.y,vm->child_position.z,vm->rotation.z,vm->scale.x,vm->scale.y,
     vm->extra_scale.x,vm->extra_scale.y,vm->sprite_size.x,vm->sprite_size.y,vm->pivot.x,vm->pivot.y};
    for(u32 i=0;i<18;++i)row[40+i]=float_bits(geometry[i]);
    row[58]=u32(vm->random_bound);row[59]=float_bits(vm->random_scale.x);row[60]=float_bits(vm->random_scale.y);
    if(vm->parent){const auto& p=*vm->parent;const float values[]={p.scale.x,p.scale.y,p.extra_scale.x,p.extra_scale.y,p.rotation.z};for(u32 i=0;i<5;++i)row[61+i]=float_bits(values[i]);}
    // This const helper writes only the local output array. It does not call
    // geometry_mode1_call or alter the emulated native-stack scratch state.
    Vec3 quad[4]{};row[66]=u32(anm_quad_positions(*vm,quad,space));
    bool visible=shot.timer.current<10;
    if(row[66])for(u32 i=0;i<4;++i){const auto p=quad[i];row[68+i*3]=float_bits(p.x);row[69+i*3]=float_bits(p.y);row[70+i*3]=float_bits(p.z);
     const float left=space.play_origin.x-192.f,top=space.play_origin.y;
     if(p.x>left&&p.x<left+384.f&&p.y>top&&p.y<top+448.f)visible=true;
    }
    row[67]=u32(visible);for(u32 i=0;i<4;++i){row[80+i]=u32(vm->integers[i]);row[84+i]=float_bits(vm->floats[i]);}
    row[88]=vm->color;row[89]=vm->secondary_color;row[90]=vm->trace_count;
    if(vm->trace_count){const auto& t=vm->trace[(vm->trace_count-1)&(anm_trace_size-1)];row[91]=t.opcode;row[92]=t.offset;}
    row[94]=vm->th13_native_flags;row[95]=u32(vm->age.previous);
   }
  }
  words.insert(words.end(),std::begin(row),std::end(row));
 }
}
}

API(shot_snapshot_enable) u32 shot_snapshot_enable(u32 value){
 if(shot_lifetime_observer::captures)return 0;
 shot_lifetime_observer::enabled=value!=0;
 if(value)shot_lifetime_observer::words.reserve(80*(4+256*96));return 1;
}
API(shot_snapshot_count) u32 shot_snapshot_count(){return shot_lifetime_observer::captures;}
API(shot_snapshot_data) const u32* shot_snapshot_data(){return shot_lifetime_observer::words.data();}

void capture(const GameBattle& b){
 observer_main_started=th14_observer_now_ns();
 ++callbacks;const auto& p=*b.player;const auto& e=b.economy;
 i32 selected[32]{};
 // Observer-only compiler fences retain the x86 recorder's logical order.
 // They neither stop the worker nor supply a gameplay value to the engine.
 const auto take=[&](u32 field,i32 value){selected[field]=value;__atomic_signal_fence(__ATOMIC_SEQ_CST);};
 take(0,b.control_frame());
 take(1,i32(p.input.movement.held));
 take(2,i32(p.input.movement.pressed));
 take(3,p.motion.state.x);
 take(4,p.motion.state.y);
 take(5,p.state.life_state);
 take(6,p.state.state_timer.current);
 take(7,p.state.transition_timer.current);
 take(8,p.state.th14_shooting_age.current);
 take(9,p.state.invincibility.current);
 take(10,p.shots.schedule.timer.current);
 take(11,p.motion.state.weapon_mode);
 take(12,e.score_units);
 take(13,e.graze);
 take(14,e.point_value);
 take(15,e.power);
 take(16,e.lives);
 take(17,e.life_fragments);
 take(18,e.th14_bombs);
 take(19,e.th14_bomb_fragments);
 take(20,e.rank);
 take(21,i32(b.animations.script_rng.seed_value()));
 take(23,i32(b.animations.visual_rng.seed_value()));
 take(22,i32(b.animations.script_rng.call_count()));
 take(24,i32(b.animations.visual_rng.call_count()));
 take(25,i32(b.enemies.count));
 u32 live=0;for(u32 i=0;i<256;++i)if(__atomic_load_n(&p.shots.at(i).state,__ATOMIC_SEQ_CST))++live;
 take(26,i32(live));
 take(27,game->state.character);
 take(28,game->state.subtype);
 take(29,game->state.difficulty);
 take(30,i32(game->state.stage));
 take(31,i32(p.th14_scale.flags));

 static_assert(sizeof(selected)==128);
 const auto start=rows.size();rows.push_back(callbacks);
 for(auto word:selected)rows.push_back(u32(word));
 const auto& c=game->compositor.world_camera;
 // Retail-order 75 words, the same public field mapping as SceneCameraReadJob.
 for(u32 i=0;i<75;++i){
  const auto offset=i<18?i*4:i<21?offsetof(SceneCamera,target_offset)+(i-18)*4:
   i==21?offsetof(SceneCamera,fov):i==22?offsetof(SceneCamera,render_width):
   i==23?offsetof(SceneCamera,render_height):offsetof(SceneCamera,view)+(i-24)*4;
  const u32 word=__atomic_load_n(reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(&c)+offset),__ATOMIC_SEQ_CST);rows.push_back(word);
 }
 const u32 hud_global=u32(th14_hud_load(e.score_units));__atomic_signal_fence(__ATOMIC_SEQ_CST);
 const u32 hud_display=u32(b.hud.score.displayed_value());rows.push_back(hud_display);rows.push_back(hud_global);
 rows.push_back(game->playback.frame());rows.push_back(game->playback.callback_frame());
 rows.push_back(game->playback.selected_stage());
 const auto* entry=game->playback.stage(game->playback.selected_stage());rows.push_back(entry?entry->frames:0);
 if(rows.size()-start!=stride)game->error="full-session observation stride mismatch";
 const u64 ended=th14_observer_now_ns();if(callbacks>300000)std::abort();
 auto* trace=observer_main_rows.data()+(callbacks-1)*8;
 trace[0]=callbacks;trace[1]=game->state.stage;trace[2]=u32(b.control_frame());
 trace[3]=u32(observer_main_started);trace[4]=u32(observer_main_started>>32);
 trace[5]=u32(ended);trace[6]=u32(ended>>32);trace[7]=0;

}
Th14WarmAttractCase warm_attract_case;
void capture_warm(const GameBattle& battle){capture(battle);
 if(!warm_attract_case.after_player_snapshot(*game))game->error="warm attract case has no battle";
 shot_lifetime_observer::capture(battle,callbacks);
 observer_published_callback.store(callbacks,std::memory_order_release);}
}
extern "C" void th14_observer_codec_warm(unsigned phase,const th11::GameSession* owner){
 if(observer_codec_warm_count>=2||phase!=observer_codec_warm_count)std::abort();
 const auto& scores=owner->scores;const auto characterBytes=sizeof(scores.characters),settingsBytes=sizeof(scores.settings);
 const auto* chars=reinterpret_cast<const u8*>(scores.characters.data());
 const auto* settings=reinterpret_cast<const u8*>(scores.settings.data());
 if(!phase){observer_live_score_snapshot.assign(chars,chars+characterBytes);observer_live_score_snapshot.insert(observer_live_score_snapshot.end(),settings,settings+settingsBytes);}
 const bool equal=!std::memcmp(chars,observer_live_score_snapshot.data(),characterBytes)&&
  !std::memcmp(settings,observer_live_score_snapshot.data()+characterBytes,settingsBytes);
 const u64 time=th14_observer_now_ns();auto* row=observer_codec_warm_rows.data()+observer_codec_warm_count*12;
 row[0]=phase;row[1]=u32(time);row[2]=u32(time>>32);
 row[3]=owner->animations.script_rng.seed_value();row[4]=owner->animations.script_rng.call_count();
 row[5]=owner->animations.visual_rng.seed_value();row[6]=owner->animations.visual_rng.call_count();
 row[7]=owner->state.stage;row[8]=u32(owner->state.phase);row[9]=u32(equal);row[10]=characterBytes;row[11]=settingsBytes;
 ++observer_codec_warm_count;
}
API(codec_warm_count) u32 codec_warm_count(){return observer_codec_warm_count;}
API(codec_warm_data) const u32* codec_warm_data(){return observer_codec_warm_rows.data();}
extern "C" void th14_observer_rng_commit(u32 point,const th11::GameSession* owner){
 const u32 index=observer_rng_events.fetch_add(1,std::memory_order_relaxed);if(index>=256)std::abort();
 auto* row=observer_rng_rows.data()+index*16;const auto& a=owner->animations;
 row[0]=index+1;row[1]=point;
 // Same post-store observer read order as the qualified x86 recorder.
 row[2]=observer_published_callback.load(std::memory_order_acquire);row[3]=owner->state.stage;
 row[5]=a.script_rng.call_count();row[7]=a.visual_rng.call_count();row[9]=u32(reinterpret_cast<std::uintptr_t>(owner));
 row[4]=a.script_rng.seed_value();row[6]=a.visual_rng.seed_value();
 row[8]=StageCppWorkerScopeTh14::owns(owner)?1:0;
 const u64 time=th14_observer_now_ns();row[10]=u32(time);row[11]=u32(time>>32);
 row[12]=0;row[13]=0;row[14]=owner->battle?owner->battle->replay_entry.seed:0;row[15]=0;
 // Main and worker reserve disjoint private slots; inspect only after joins.
}
API(observer_rng_count) u32 observer_rng_count(){return observer_rng_events.load(std::memory_order_acquire);}
API(observer_rng_data) const u32* observer_rng_data(){return observer_rng_rows.data();}
API(observer_main_count) u32 observer_main_count(){return callbacks;}
API(observer_main_data) const u32* observer_main_data(){return observer_main_rows.data();}
extern "C" void emscripten_runtime_keepalive_push(){++keepalive;++pushes;}
extern "C" void emscripten_runtime_keepalive_pop(){if(keepalive<=0)std::abort();--keepalive;++pops;}
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(begin) u32 begin(u32 ticks,u32 cookie,u32 warm){
 if(current||!NativeStackTh14::preinitialized_cookie(cookie))return 0;
 current=std::make_unique<Application>();game=&current->session;
 if(current->initial_ticks!=ticks){current->error="initial clock input mismatch";return 0;}
 current->process_cookie=cookie;
 callbacks=0;rows.clear();shot_lifetime_observer::captures=0;shot_lifetime_observer::words.clear();
 if(warm)warm_attract_case.arm();
 if(!current->initialize())return 0;
 observer_frame_cadence.reset();observer_frame_opportunities=observer_outer_ticks=0;
 observer_frame_rows.clear();observer_frame_rows.reserve(30000*14);

 // Preserve the existing stage initialization callback. Install only the
 // observer pointer when the real battle starts creating its first VMs.
 auto previous=game->animations.before_initial_update;
 game->animations.before_initial_update=[previous](const AnmVm& vm){
  if(!StageCppWorkerScopeTh14::owns(game)&&game->battle)game->battle->before_player_update=capture_warm;
  return !previous||previous(vm);
 };
 return 1;
}
API(tick) u32 tick(){return current->tick_once(0);}

namespace {
Replay fixture_keys;
bool fixture_keys_enabled=false;
u32 fixture_key_reads=0,fixture_key_tail_reads=0,fixture_last_key_stage=0,fixture_last_key_frame=0,fixture_last_key=0;
u32 fixture_physical_held(){
 if(!fixture_keys_enabled||!current)return menu_input_held;
 const auto& session=current->session;
 if((session.state.phase!=GameSessionPhase::stage&&session.state.phase!=GameSessionPhase::loading)||session.state.replay||session.state.demo)return menu_input_held;
 // Read the ordinary recorder's own input position. No replay header is
 // restored into the game: this separate decoder supplies key masks only.
 u32 stage=session.recording.selected?session.recording.selected:session.state.stage;
 const auto* entry=fixture_keys.stage(stage);
 if(!entry||stage>=session.recording.stages.size())return menu_input_held;
 u32 frame=session.recording.selected==stage?session.recording.stages[stage].frames:0;
 // The next ordinary Control pass can activate inside tick_once, after
 // physical keys have been sampled. Supply its first keys when the prior
 // input segment has finished; do not restore any recorded game state.
 if(stage!=session.state.stage&&frame>=entry->frames){
  const auto* incoming=fixture_keys.stage(session.state.stage);
  if(incoming){stage=session.state.stage;entry=incoming;frame=0;}
 }
 fixture_last_key_stage=stage;fixture_last_key_frame=frame;++fixture_key_reads;
 u32 held=1; // after the supplied segment, keep shooting rather than all-FF keys
 if(frame<entry->frames){
  const auto* p=fixture_keys.decoded().data()+entry->offset+kReplayStageHeader+frame*6;
  const bool terminal=p[0]==255&&p[1]==255&&p[2]==255&&p[3]==255&&p[4]==255&&p[5]==255;
  if(!terminal)held=u32(p[0])|u32(p[1])<<8;else ++fixture_key_tail_reads;
 }else ++fixture_key_tail_reads;
 fixture_last_key=held;return held;
}
}
API(load_keys) u32 load_keys(const u8* data,u32 size){
 if(!fixture_keys.open(data,size)||fixture_keys.character()>2||fixture_keys.subtype()>1||fixture_keys.difficulty()!=4||fixture_keys.stage_count()!=1||!fixture_keys.stage(7)||fixture_keys.uses_touch())return 0;
 if(fixture_keys.decoded()[10]&3)return 0;
 fixture_keys_enabled=true;return 1;
}
API(keyscript_state) const u32* keyscript_state(){
 static u32 w[12];const auto& s=current->session;
 w[0]=fixture_keys_enabled;w[1]=fixture_last_key_stage;w[2]=fixture_last_key_frame;w[3]=fixture_last_key;
 w[4]=fixture_key_reads;w[5]=fixture_key_tail_reads;w[6]=s.state.replay;w[7]=s.recording_active;
 w[8]=s.completed_run;w[9]=s.recording.selected;w[10]=w[9]<s.recording.stages.size()?s.recording.stages[w[9]].frames:0;w[11]=s.state.stage;
 return w;
}
API(ordinary_flow_state) const u32* ordinary_flow_state(){
 static u32 w[24];auto& s=current->session;
 w[0]=u32(s.state.phase);w[1]=s.state.stage;w[2]=s.state.replay;w[3]=s.ending?u32(s.ending->index):~0u;
 w[4]=s.ending?s.ending->seen:0;w[5]=s.title?u32(s.title->screen):~0u;w[6]=s.completed_run;
 w[7]=u32(s.clear_records.clears[fixture_keys.character()*2+fixture_keys.subtype()][4]);w[8]=u32(s.clear_records.no_continue_clears[fixture_keys.character()*2+fixture_keys.subtype()][4]);
 w[9]=s.scores.settings[0x16];w[10]=s.scores.settings[0x17+fixture_keys.character()*2+fixture_keys.subtype()];w[11]=s.title?u32(s.title->unlocked()):0;
 for(i32 n=0;n<6;++n)w[12+n]=s.title?u32(s.title->available(n/2,n%2)):0;
 w[18]=callbacks;w[19]=s.battle?u32(s.battle->completion.state.exit):0;
 w[20]=s.battle?u32(s.battle->completion.state.ending_frames):0;w[21]=s.battle?u32(bool(s.battle->pending_stage)):0;
 w[22]=s.state.frame;w[23]=s.title?u32(s.title->substate):~0u;return w;
}

API(frame) u32 frame(double seconds){
 ++observer_frame_opportunities;
 const u32 ticks=observer_frame_cadence.advance(seconds),before=callbacks;
 const u64 entered=ticks?th14_observer_now_ns():0;bool ok=true;u32 passes=0,repeats=0;
 current->graphics.backend.defer=true;
 for(u32 n=0;n<ticks&&ok;++n){
  // Actual sample_and_tick control flow, with the declared held=0 input.
  do{const bool pause=menu_pause_pending;menu_pause_pending=false;ok=current->tick_once(fixture_physical_held(),pause);++passes;if(ok&&current->repeat_update)++repeats;}
  while(ok&&current->repeat_update);
 }
 current->graphics.backend.commit();current->graphics.backend.defer=false;
 current->audio.pump();
 if(ticks){
  ++observer_outer_ticks;const u64 ended=th14_observer_now_ns();u64 delta;std::memcpy(&delta,&seconds,8);
  const u32 row[]={observer_frame_opportunities,observer_outer_ticks,before,callbacks,passes,repeats,ticks,
   u32(entered),u32(entered>>32),u32(ended),u32(ended>>32),u32(delta),u32(delta>>32),u32(ok)};
  observer_frame_rows.insert(observer_frame_rows.end(),std::begin(row),std::end(row));
 }
 return ok;
}
API(frame_tick_count) u32 frame_tick_count(){return observer_outer_ticks;}
API(frame_opportunity_count) u32 frame_opportunity_count(){return observer_frame_opportunities;}
API(frame_trace_words) u32 frame_trace_words(){return u32(observer_frame_rows.size());}
API(frame_trace_data) const u32* frame_trace_data(){return observer_frame_rows.data();}

API(audio_pump) void audio_pump(){current->audio.pump();}
API(observation_count) u32 observation_count(){return callbacks;}
API(observation_data) const u32* observation_data(){return rows.data();}
API(observation_words) u32 observation_words(){return u32(rows.size());}
API(error_data) const char* error_data(){return current?current->error.data():"no Application";}
API(error_size) u32 error_size(){return current?u32(current->error.size()):14;}
API(state) const u32* state(){static u32 w[16];auto& a=*current;
 w[0]=a.boot_signature_draws;w[1]=a.boot_loading.handle;w[2]=a.session.animations.script_rng.call_count();
 w[3]=a.session.animations.script_rng.seed_value();w[4]=a.boot_upload_index;w[5]=a.boot_signature_active;
 w[6]=bool(a.boot_cpp_resources);w[7]=bool(a.title_cpp_resources);w[8]=bool(a.audio_cpp_boot);
 w[9]=u32(a.session.state.phase);w[10]=a.session.state.stage;w[11]=a.session.state.frame;
 w[12]=u32(keepalive);w[13]=pushes;w[14]=pops;w[15]=callbacks;return w;}
API(close) void close_fixture(){current.reset();game=nullptr;}

// Read-only Main/worker lifetime facts. The host sends one ordinary close input
// after observing a real returned callback with a retained loading owner.
API(close_gate_state) const u32* close_gate_state(){
 auto& a=*current;auto& s=a.session;static u32 w[20];
 w[0]=s.has_cpp_stage_worker();w[1]=u32(s.stage_cpp_worker_result());
 w[2]=a.initial_upload_waiting;w[3]=bool(a.boot_stage_owner);w[4]=s.battle?s.battle->pending_stage:0;
 w[5]=bool(s.resources.loading_bundle());w[6]=u32(s.state.phase);w[7]=s.state.stage;w[8]=s.state.frame;
 w[9]=u32(s.animations.first_deferred_capture_file_index());w[10]=a.cpp_menu_close_started;w[11]=a.cpp_menu_close_done;
 w[12]=__atomic_load_n(&s.stage_load_host_flags,__ATOMIC_ACQUIRE);w[13]=a.stage_uploads.pending_count();
 w[14]=s.animations.script_rng.seed_value();w[15]=s.animations.script_rng.call_count();
 w[16]=s.animations.visual_rng.seed_value();w[17]=s.animations.visual_rng.call_count();w[18]=callbacks;w[19]=u32(a.error.size());return w;
}
API(request_host_close) void request_host_close(){current->session.request_host_close();}

API(campaign_end_state) const u32* campaign_end_state(){
 auto& s=current->session;auto* p=s.pause_menu.get();static u32 w[18];
 w[0]=u32(s.state.phase);w[1]=s.state.stage;w[2]=u32(s.state.replay);w[3]=u32(bool(p));
 w[4]=p?u32(p->state):0xffffffff;w[5]=p?u32(p->timer.current):0xffffffff;
 w[6]=p?u32(p->forced_exit):0xffffffff;w[7]=p?u32(p->cursor.selected):0xffffffff;
 w[8]=p?u32(p->cursor.count):0xffffffff;w[9]=p?u32(p->cursor.disabled_count):0xffffffff;
 w[10]=s.playback.frame();w[11]=s.playback.callback_frame();w[12]=s.playback.selected_stage();
 const auto* entry=s.playback.stage(s.playback.selected_stage());w[13]=entry?entry->frames:0;
 w[14]=u32(s.playback.current().end_marker);w[15]=s.battle?u32(s.battle->enemy_commands.th14_run_flags):0u;
 w[16]=p?u32(p->replay):0;w[17]=callbacks;return w;
}

API(async_deliver_owned) void async_deliver_owned(u32 callback,u32 data){th14_async_invoke(callback,data);}

API(set_menu_input) void set_menu_input(u32 held){menu_input_held=held;}
API(menu_state) const u32* menu_state(){
 auto& s=current->session;auto* t=s.title.get();static u32 w[10];
 w[0]=t?u32(t->screen):0xffffffff;w[1]=t?u32(t->substate):0xffffffff;w[2]=t?u32(t->cursor.selected):0xffffffff;
 w[3]=t?u32(t->selection.character):0xffffffff;w[4]=t?u32(t->selection.partner):0xffffffff;w[5]=t?u32(t->selection.difficulty):0xffffffff;
 w[6]=u32(s.state.phase);w[7]=u32(s.state.character);w[8]=u32(s.state.subtype);w[9]=u32(s.state.difficulty);return w;
}

API(press_pause) void press_pause(){menu_pause_pending=true;}
API(behavior_state) const u32* behavior_state(){
 auto& s=current->session;auto* b=s.battle.get();auto* p=b?b->player.get():nullptr;static u32 w[20];
 w[0]=u32(s.state.phase);w[1]=s.state.stage;w[2]=s.state.character;w[3]=s.state.subtype;w[4]=s.state.difficulty;
 w[5]=b?u32(b->control_frame()):0;w[6]=p?u32(p->motion.state.x):0;w[7]=p?u32(p->motion.state.y):0;
 w[8]=p?u32(p->state.life_state):0xffffffff;w[9]=b?u32(b->economy.th14_bombs):0xffffffff;
 w[10]=b&&b->bomb?u32(b->bomb->state.active):0;w[11]=0;
 if(p)for(u32 i=0;i<256;++i)if(p->shots.at(i).state)++w[11];
 w[12]=p?u32(p->motion.state.focused):0;w[13]=p?u32(p->input.movement.held):0;
 w[14]=s.pause_menu?u32(s.pause_menu->state):0xffffffff;w[15]=callbacks;
 w[16]=p?u32(p->motion.state.normal_speed):0;w[17]=p?u32(p->motion.state.focus_speed):0;
 w[18]=b?u32(b->economy.power):0;w[19]=b?u32(b->economy.lives):0;
 return w;
}

API(flush_save) u32 flush_save(){return current->save_scores();}
API(config_data) const u8* config_data(){return current->session.persistent_config().bytes.data();}
API(score_semantics_data) const u8* score_semantics_data(){
 static std::vector<u8> w;w.clear();auto& scores=current->session.scores;
 for(const auto& c:scores.characters)w.insert(w.end(),c.begin(),c.end());
 w.insert(w.end(),scores.settings.begin(),scores.settings.end());return w.data();
}
API(score_semantics_size) u32 score_semantics_size(){return 7*ScoreFile::character_size+ScoreFile::settings_size;}

API(pause_save_state) const u32* pause_save_state(){
 auto* p=current->session.pause_menu.get();static u32 w[12];
 w[0]=p?u32(p->state):0xffffffff;w[1]=p?u32(p->timer.current):0;
 w[2]=p?u32(p->cursor.selected):0;w[3]=p?u32(p->cursor.count):0;
 w[4]=p?u32(p->name_cursor.selected):0;w[5]=p?u32(p->name_length):0;
 w[6]=p?u32(p->save_requested):0;w[7]=p?u32(p->replay):0;
 w[8]=u32(current->session.state.replay);w[9]=callbacks;w[10]=current->session.playback.frame();w[11]=current->session.playback.callback_frame();return w;
}

API(viewer_ready) u32 viewer_ready(){return current->hosted_replay_open_ready();}
API(viewer_open) u32 viewer_open(const u8* p,u32 n,u32 stage){return current->open_hosted_replay(p,n,stage);}
API(viewer_status) const u32* viewer_status(){return current->hosted_replay_status();}
API(viewer_seek) i32 viewer_seek(u32 target,u32 budget){return current->hosted_replay_seek_step(target,budget);}
API(viewer_rate) u32 viewer_rate(double rate){return current->set_hosted_replay_rate(rate);}
API(viewer_close) void viewer_close(){current->close_hosted_replay();}
API(viewer_clock) u32 viewer_clock(double seconds){return current->hosted_cadence.advance(seconds,current->hosted_replay_rate);}
API(viewer_alloc) void* viewer_alloc(u32 size){return std::malloc(size);}
API(viewer_free) void viewer_free(void* p){std::free(p);}
API(viewer_describe) const char* viewer_describe(const u8* p,u32 n){static std::string result,error;return describe_replay_th14(p,n,result,error)?result.c_str():nullptr;}

API(outcome_state) const u32* outcome_state(){
 auto& s=current->session;auto& e=s.economy;static u32 w[12];
 w[0]=u32(th14_hud_load(e.score_units));w[1]=s.battle?u32(s.battle->hud.score.displayed_value()):0;
 w[2]=u32(e.lives);w[3]=u32(e.life_fragments);w[4]=u32(e.th14_bombs);w[5]=u32(e.th14_bomb_fragments);w[6]=u32(e.power);w[7]=u32(e.graze);
 w[8]=s.battle?u32(s.battle->completion.state.displayed_bonus):0;w[9]=s.battle?s.battle->completion.state.hud_flags:0;w[10]=u32(s.state.stage);w[11]=u32(s.state.phase);return w;
}

API(ordinary_timing_state) const u32* ordinary_timing_state(){
 static u32 w[8];auto& s=current->session;auto* b=s.battle.get();
 w[0]=u32(s.state.phase);w[1]=s.state.stage;w[2]=s.recording.selected;
 w[3]=b&&b->stage_active;w[4]=b&&bool(b->pending_stage);w[5]=b?u32(b->resources.stage_number):0;w[6]=b?u32(b->control_frame()):0;
 w[7]=(s.state.phase==GameSessionPhase::stage&&b&&b->stage_active&&!b->pending_stage&&b->resources.stage_number==i32(s.state.stage)&&s.recording.selected==s.state.stage)||(s.state.phase==GameSessionPhase::ending&&s.ending&&s.ending->active&&!s.ending->resource_loading());
 return w;
}
API(recorded_stage_seeds) const u32* recorded_stage_seeds(){
 static u32 w[8*4];const auto& s=current->session;
 for(u32 n=0;n<8;n++){
  const auto& stage=s.recording.stages[n];const auto* p=stage.header.data();auto* out=w+n*4;
  out[0]=stage.present;out[1]=u32(p[2])|(u32(p[3])<<8);out[2]=stage.frames;out[3]=fixture_keys.stage(n)?u32(fixture_keys.header(n)[2])|(u32(fixture_keys.header(n)[3])<<8):0;
 }return w;
}

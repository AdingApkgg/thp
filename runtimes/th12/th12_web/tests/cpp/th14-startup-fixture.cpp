#include "th14-config-session-fixture.cpp"
#include "../../cpp/game/LoadingTh14.hpp"
#include "../../cpp/game/ClockSeedTh14.hpp"
#include "../../cpp/game/MusicCatalog.hpp"
struct TitleManualEffects:StageResourceEffects {
    std::vector<std::vector<u8>> images;u32 releases=0;
    bool prepare_manual_image(AnmResource&,u32 index,const u8* bytes,u32 size)override{
        if(index!=1||size<24||std::memcmp(bytes,"\x89PNG\r\n\x1a\n",8))return false;
        images.emplace_back(bytes,bytes+size);return true;
    }
    void release_animation(AnmResource&)override{++releases;}
};
static TitleManualEffects title_manual_effects;
API(manual_session_begin) u32 manual_session_begin(){session.resources.effects=nullptr;if(!session.open_title(source,false))return 0;title_manual_effects={};session.resources.effects=&title_manual_effects;return 1;}
API(manual_session_value) u32 manual_session_value(u32 field){const auto* m=session.title_manual.get();switch(field){case 0:return u32(session.state.phase);case 1:return session.title?u32(session.title->screen):u32(-1);case 2:return session.title?session.title->substate:u32(-1);case 3:return m?1:0;case 4:return m?m->manual_phase:u32(-1);case 5:return m?m->manual_substate:u32(-1);case 6:return m?m->manual_cursor.selected:u32(-1);case 7:return m?m->manual_timer.current:u32(-1);case 8:return title_manual_effects.images.size();case 9:return title_manual_effects.releases;case 10:return m?float_bits(m->manual_origin_x):0;case 11:return session.title?session.title->cursor.selected:u32(-1);default:return 0;}}
API(manual_session_image) const u8* manual_session_image(u32 n){return title_manual_effects.images[n].data();}
API(manual_session_image_size) u32 manual_session_image_size(u32 n){return title_manual_effects.images[n].size();}
API(manual_session_reset) u32 manual_session_reset(){return session.open_title(source,false);}
API(clock_apply) const u32* clock_apply(u32 ticks,u32 calls){static Rng pair[2];pair[0]={0xbeef,0x4321,calls};pair[1]={0xabcd,0x1234,calls^0x80000000u};th14_seed_clock(ticks,pair[0],pair[1]);return reinterpret_cast<const u32*>(pair);}
static std::unique_ptr<GameSession> clock_session;
static AnmManager template_manager;
static AnmResource template_resource;
static AnmVm template_copy;
API(template_reset) u32 template_reset(u32 seed,u32 calls){template_manager.clear();template_manager.fallback_sprites=&session.resources.core.ascii;template_manager.script_rng={u16(seed),0,calls};template_resource=session.resources.core.effect;template_resource.templates.reset();return template_manager.prepare_resource(template_resource,8);}
API(template_rng) u32 template_rng(u32 field){return field?template_manager.script_rng.calls:template_manager.script_rng.seed;}
API(template_disable) void template_disable(u32 mask){auto& c=session.resources.core;if(mask&1)for(auto& p:c.players)p.templates.reset();if(mask&2)c.effect.templates.reset();if(mask&4){c.ascii.templates.reset();c.bullet.templates.reset();c.enemy.templates.reset();c.front.templates.reset();c.text.templates.reset();c.title.templates.reset();c.title_variant.templates.reset();}if((mask&8)&&session.resources.stage){auto& s=*session.resources.stage;s.background.templates.reset();s.logo.templates.reset();s.enemies.templates.reset();for(auto& a:s.ecl_animations)a.templates.reset();}}
API(template_bind) u32 template_bind(){template_copy={};template_copy.position={320,400,-8};return template_copy.copy_script(template_resource,21,8,&template_manager.rate);}
API(template_raw_bind) u32 template_raw_bind(){template_copy={};template_copy.position={320,400,-8};return template_copy.bind_script(template_resource,21,8,&template_manager.rate);}
API(template_update) i32 template_update(){return template_copy.update(template_manager);}
static AnmVm template_parent;
API(template_factory) u32 template_factory(u32 detached,u32 flags){template_manager.clear();template_parent={};template_parent.initialize();template_parent.resource=&template_resource;template_parent.file_index=8;template_parent.layer=27;template_parent.flags2=0x1000000;template_parent.position={320,400,-8};template_parent.rotation={.25f,-.5f,.75f};template_parent.script_position={12,-34,56};auto* vm=template_manager.spawn(template_parent,21,detached?95:flags==6?92:flags==4?90:88);if(!vm)return 0;template_copy=*vm;return 1;}
API(template_factory_state) u32 template_factory_state(u32 field){const auto& v=template_copy;const u32 values[]={v.flags2,v.parent?1u:0u,float_bits(v.rotation.x),float_bits(v.rotation.y),float_bits(v.rotation.z),float_bits(v.child_position.x),float_bits(v.child_position.y),float_bits(v.child_position.z)};return values[field];}
API(template_state) u32 template_state(u32 field,u32 bound){const auto& v=bound?template_copy:template_resource.templates->scripts[21];const u32 values[]={u32(v.integers[0]),u32(v.integers[1]),v.layer,v.color,u32(v.timer.current),float_bits(v.timer.fractional),float_bits(v.script_position.x),float_bits(v.script_position.y),float_bits(v.script_position.z),float_bits(v.scale.x),float_bits(v.scale.y),float_bits(v.random_scale.x),float_bits(v.random_scale.y),u32(v.random_bound),u32(reinterpret_cast<const u8*>(v.instruction)-reinterpret_cast<const u8*>(v.script_begin)),float_bits(v.position.x),float_bits(v.position.y),float_bits(v.position.z)};return values[field];}
API(clock_construct) const u8* clock_construct(u32 ticks){clock_session=std::make_unique<GameSession>(ticks);return clock_session->font_bitmap.noise.data();}
API(clock_construct_state) u32 clock_construct_state(u32 field){switch(field){case 0:return clock_session->animations.script_rng.seed;case 1:return clock_session->animations.script_rng.calls;case 2:return clock_session->animations.visual_rng.seed;case 3:return clock_session->animations.visual_rng.calls;default:return 0;}}
static LoadingTh14 loading;
static u32 loading_root=0;
API(loading_reset) void loading_reset(){loading={};loading_root=0;session.animations.clear();}
API(loading_begin) u32 loading_begin(float x,float y){const bool ok=loading.begin(session.animations,session.resources.core.ascii,x,y);loading_root=loading.handle;return ok;}
API(loading_finish) void loading_finish(){loading.finish(session.animations);}
API(loading_state) u32 loading_state(u32 field){auto* vm=session.animations.find(loading.handle);switch(field){case 0:return loading.handle;case 1:return vm?float_bits(vm->position.x):0;case 2:return vm?float_bits(vm->position.y):0;case 3:return vm?vm->layer:0;default:return 0;}}
API(loading_tick) u32 loading_tick(){return session.animations.update(true)&&session.animations.update(false);}
API(loading_root_state) u32 loading_root_state(u32 field){auto* vm=session.animations.find(loading_root);switch(field){case 0:return vm?1:0;case 1:return vm?vm->timer.current:0;case 2:return vm?vm->pending_interrupt:0;default:return 0;}}
struct DeferredEffects:StageResourceEffects {
    bool done=false;
    bool prepare(StageResources&)override{loading={};const bool ok=loading.begin(session.animations,session.resources.core.ascii);loading_root=loading.handle;return ok;}
    bool stage_ready()const override{return done;}
};
static DeferredEffects deferred;
struct DeferredCoreEffects:StageResourceEffects {bool done=false;bool core_ready()const override{return done;}};
static DeferredCoreEffects deferred_core;
static std::unique_ptr<GameSession> core_session;
static LoadingTh14 core_loading;
API(core_begin) u32 core_begin(u32 ticks){core_session=std::make_unique<GameSession>(ticks);deferred_core.done=false;core_session->resources.effects=&deferred_core;core_loading={};return core_session->open_title(source,true)&&core_loading.begin(core_session->animations,core_session->resources.core.ascii);}
API(core_state) u32 core_state(u32 field){auto& s=*core_session;switch(field){case 0:return u32(s.state.phase);case 1:return s.title?1:0;case 2:return s.resources.core.effect.templates?1:0;case 3:return s.animations.script_rng.calls;case 4:return s.animations.script_rng.seed;case 5:return s.animations.visual_rng.calls;case 6:return s.state.frame;case 7:return s.title?u32(s.title->timer.current):0xffffffffu;case 8:return s.animations.active_count();default:return 0;}}
API(core_decoded) u32 core_decoded(){auto& c=core_session->resources.core;const AnmResource* files[]={&c.effect,&c.bullet,&c.enemy,&c.front,&c.title,&c.title_variant,&c.players[0],&c.players[1],&c.players[2]};u32 mask=0;for(u32 i=0;i<9;++i)if(!files[i]->scripts.empty())mask|=1u<<i;return mask;}
API(core_job) u32 core_job(u32 index){auto& s=*core_session;auto& c=s.resources.core;AnmResource* files[]={&c.effect,&c.bullet,&c.enemy,&c.front,&c.title,&c.title_variant,&c.players[0],&c.players[1],&c.players[2]};constexpr u16 ids[]={8,7,9,5,24,25,7,7,7};return index<9&&s.resources.load_core_job(index)&&s.animations.prepare_resource(*files[index],ids[index]);}
API(core_tick) u32 core_tick(u32 held){auto& s=*core_session;if(s.state.phase==GameSessionPhase::loading&&(!s.animations.update(true)||!s.animations.update(false)))return 0;return s.update({held,0,0})&&s.draw(renderer);}
API(core_finish) u32 core_finish(){core_loading.finish(core_session->animations);deferred_core.done=true;return core_session->finish_loading();}
API(deferred_demo) u32 deferred_demo(u32 index){deferred.done=false;session.resources.effects=&deferred;return begin_demo(index);}
static std::vector<std::pair<AnmResource*,u16>> deferred_jobs(){auto& s=*session.resources.stage;std::vector<std::pair<AnmResource*,u16>> out={{&s.background,u16((s.stage_number&1)+3)},{&s.logo,6},{&s.enemies,9}};for(u32 i=0;i<s.ecl_animations.size();++i)if(!s.ecl_animation_names[i].empty())out.push_back({&s.ecl_animations[i],u16(10+i)});return out;}
API(deferred_job_count) u32 deferred_job_count(){return u32(deferred_jobs().size());}
API(deferred_templates) u32 deferred_templates(){u32 mask=0,index=0;for(const auto& job:deferred_jobs()){if(job.first->templates)mask|=1u<<index;++index;}return mask;}
API(deferred_job) u32 deferred_job(u32 index){const auto jobs=deferred_jobs();return index<jobs.size()&&session.animations.prepare_resource(*jobs[index].first,jobs[index].second);}
API(deferred_finish) u32 deferred_finish(){loading.finish(session.animations);deferred.done=true;const bool ok=session.finish_loading();session.resources.effects=nullptr;return ok;}
API(deferred_state) u32 deferred_state(u32 field){switch(field){case 0:return session.battle?1:0;case 1:return session.ready()?1:0;case 2:return session.animations.visual_rng.seed;case 3:return session.animations.visual_rng.calls;default:return 0;}}
static GameBattle* transition_world=nullptr;
static PlayerFrame* transition_player=nullptr;
API(transition_begin) u32 transition_begin(u32 stage,u32 selection){session.resources.effects=nullptr;if(!session.begin(source,stage-1,selection>>1,selection&1,1))return 0;transition_world=session.battle.get();transition_player=session.battle->player.get();if(!session.battle->dialogue_stage_complete())return 0;deferred.done=false;session.resources.effects=&deferred;return session.update({})&&session.state.phase==GameSessionPhase::loading;}
API(transition_state) u32 transition_state(u32 field){auto* b=session.battle.get();if(!b)return 0;const u32 values[]={b==transition_world,b->player.get()==transition_player,b->frame,u32(b->transition_timer.current),b->stage_active,b->transitioning,b->pending_stage,u32(b->player->state.state_timer.current),u32(b->player->motion.state.x),u32(b->player->motion.state.y),u32(session.economy.power),u32(session.economy.score_units),u32(session.economy.lives),u32(session.economy.th14_bombs)};return values[field];}
API(stage_music_begin) u32 stage_music_begin(u32 stage,u32 frame){session.resources.effects=nullptr;if(!session.begin(source,stage,0,0,1))return 0;session.battle->frame=frame;return 1;}
API(stage_music_events) u32 stage_music_events(u32 resume){u32 count=0;if(session.battle)for(const auto& event:session.battle->events)if(event.kind==(resume?BattleEventKind::MusicResume:BattleEventKind::StageMusic))++count;return count;}
static LoadingTh14 ending_loading;
struct EndingLoadingEffects:StageResourceEffects {
    bool defer_ending_loading()const override{return true;}
    bool begin_ending_loading()override{return ending_loading.begin(session.animations,session.resources.core.ascii);}
    void finish_ending_loading()override{ending_loading.finish(session.animations);}
};
static EndingLoadingEffects ending_loading_effects;
static std::unique_ptr<Ending> ending_loading_test;
static std::array<u8,28> ending_loading_code;
static std::array<u32,14> ending_loading_words;
API(ending_loading_begin) u32 ending_loading_begin(u32 slot,float rate,u32 seen){
    ending_loading_test.reset();session.animations.clear();session.animations.rate=rate;ending_loading={};
    ending_loading_test=std::make_unique<Ending>(session.animations,session.resources.core.text,session.scores);
    auto& e=*ending_loading_test;if(!e.begin(source,0,1,0))return 0;
    e.effects=&ending_loading_effects;e.seen=seen;
    ending_loading_code.fill(0);auto* p=ending_loading_code.data();p[2]=7;p[3]=12;std::memcpy(p+4,&slot,4);std::memcpy(p+8,"e01.anm",8);p[18]=9;p[19]=4;const u32 ink=0x123456;std::memcpy(p+20,&ink,4);p[24]=p[25]=255;e.instruction=p;e.end=p+ending_loading_code.size();return 1;
}
API(ending_loading_tick) u32 ending_loading_tick(){return ending_loading_test->tick(0,0);}
API(ending_loading_complete) u32 ending_loading_complete(){return ending_loading_test->finish_resource_loading();}
API(ending_loading_state) const u32* ending_loading_state(){const auto& e=*ending_loading_test;auto& r=ending_loading_words;r[0]=u32(e.instruction-ending_loading_code.data());r[1]=e.flags;r[2]=e.line;r[3]=e.color;r[4]=e.frames;u32 i=5;for(const Timer* t:{&e.elapsed,&e.time,&e.wait}){r[i++]=u32(t->previous);r[i++]=u32(t->current);r[i++]=float_bits(t->fractional);}return r.data();}
API(ending_loading_resource) u32 ending_loading_resource(u32 field){const auto& e=*ending_loading_test;switch(field){case 0:return e.resources.size();case 1:return e.resource_loading();case 2:return ending_loading.handle;case 3:for(auto* s:e.slots)if(s)return s->templates?1:0;return 0;default:return 0;}}
API(ending_session_begin) u32 ending_session_begin(u32 selection,i32 continues){session.resources.effects=nullptr;if(!session.begin(source,6,selection>>1,selection&1,1))return 0;ending_loading={};session.resources.effects=&ending_loading_effects;session.battle->hud.score.continues=continues;return session.battle->dialogue_stage_complete();}
API(ending_session_state) u32 ending_session_state(u32 field){auto* e=session.ending.get();if(!e)return 0;switch(field){case 0:return e->index;case 1:return e->resource_loading();case 2:return e->flags;case 3:return u32(e->time.current);case 4:return u32(e->elapsed.current);case 5:return e->frames;case 6:return e->resources.size();case 7:return e->instruction?u32(e->instruction-e->messages[e->message].data()):0;case 8:return e->resource_loading_name()=="staff.anm"?1:0;default:return 0;}}
API(ending_session_complete) u32 ending_session_complete(){return session.ending&&session.ending->finish_resource_loading();}
static u32 results_creation_first=0;
API(results_probe_setup) u32 results_probe_setup(u32 selection,u32 difficulty,i32 continues,u32 screen,u32 substate,u32 timer){
    session.animations.clear();Rng rng{};session.scores.initialize(rng);
    auto& r=session.resources.core;session.title=std::make_unique<TitleMenu>(session.animations,r.title,r.title_variant,r.ascii,session.scores);
    auto& t=*session.title;t.flags=0;t.screen=TitleScreen(screen);t.substate=substate;t.timer.set(i32(timer),&session.animations.rate);
    t.selection.character=selection>>1;t.selection.partner=selection&1;t.selection.difficulty=difficulty;t.result_continues=continues;
    t.cursor.count=30;t.cursor.select(2);t.name_cursor.count=91;t.name_cursor.wrap=1;results_creation_first=anm_creation_count();return 1;
}
API(results_probe_rank) void results_probe_rank(i32 rank){auto& t=*session.title;auto& record=session.scores.characters[t.selection.character*2+t.selection.partner];
    for(u32 row=0;row<10;++row){const u32 score=row<9?2000000:1;std::memcpy(record.data()+0x10+(t.selection.difficulty*10+row)*28,&score,4);}
    t.result_score=rank<0?0:rank==0?3000000:1;
}
API(results_probe_name) void results_probe_name(u32 selected,u32 length){auto& t=*session.title;t.name_cursor.select(selected);t.name_length=length;std::memcpy(t.entered_name.data(),"ABCDEFGH",9);}
API(results_probe_tick) u32 results_probe_tick(u32 pressed,u32 repeat){return session.title->update(pressed,repeat);}
API(results_probe_value) i32 results_probe_value(u32 field){auto& t=*session.title;switch(field){case 0:return i32(t.screen);case 1:return t.substate;case 2:return t.cursor.selected;case 3:return t.name_cursor.selected;case 4:return t.name_length;case 5:return t.result_unranked;case 6:return t.music_request;case 7:return t.sounds.size();case 8:return t.sounds.empty()?-1:t.sounds.front();case 9:return anm_creation_count()-results_creation_first;case 10:return t.handles[100]!=0;case 11:return t.handles[101]!=0;case 12:return t.handles[261]!=0;default:return -1;}}
API(results_probe_name_bytes) const char* results_probe_name_bytes(){return session.title->entered_name.data();}
API(results_probe_saved_name) const u8* results_probe_saved_name(){return session.scores.settings.data()+12;}
API(results_probe_creation) i32 results_probe_creation(u32 index,u32 field){return anm_creation_value(results_creation_first+index,field);}
static std::unique_ptr<AsciiText> results_text;
API(results_text_records) u8* results_text_records(){auto& t=*session.title;return session.scores.characters[t.selection.character*2+t.selection.partner].data()+0x10+t.selection.difficulty*0x118;}
API(results_text_queue) u32 results_text_queue(u32 selected,u32 unranked){auto& t=*session.title;t.cursor.select(selected);t.result_unranked=unranked;results_text=std::make_unique<AsciiText>(session.resources.core.ascii);t.queue_ascii(*results_text);return results_text->requests.size();}
API(results_text_bytes) const char* results_text_bytes(u32 index){return results_text->requests[index].text.c_str();}
API(results_text_value) u32 results_text_value(u32 index,u32 field){auto& r=results_text->requests[index];const u32 values[]={float_bits(r.position.x),float_bits(r.position.y),float_bits(r.position.z),r.style.color,u32(r.style.shadow),u32(r.style.font),float_bits(r.style.scale.x),float_bits(r.style.scale.y)};return values[field];}
API(records_probe_setup) u32 records_probe_setup(u32 selection,u32 difficulty,u32 page,u32 substate,u32 timer){
    results_probe_setup(0,1,0,10,substate,timer);auto& t=*session.title;t.text_resource=&session.resources.core.text;
    for(auto& c:session.scores.characters)c.fill(0);session.scores.settings.fill(0);
    for(u32 c=0;c<7;++c)for(u32 id=0;id<120;++id){auto* p=session.scores.characters[c].data()+0x978+id*0x9c;std::snprintf(reinterpret_cast<char*>(p),128,"Spell %03u\x81\x48",id);const u32 capture=(id+c)%3,seen=id%3?7:0;std::memcpy(p+0x80,&capture,4);std::memcpy(p+0x88,&seen,4);}
    t.cursor.count=6;t.cursor.wrap=1;t.cursor.select(selection);t.secondary.count=5;t.secondary.wrap=1;t.secondary.select(difficulty);
    u32 n=0;for(u32 id=0;id<120;++id)if((id<26?(id+2)%4:id<108?id%4:4)==difficulty)++n;
    t.page.count=(n+9)/10+1;t.page.wrap=1;t.page.select(page);
    if(substate==2){const auto first=anm_creation_count();for(u32 row=0;row<10;++row){auto* vm=session.animations.create(session.resources.core.text,3+row,0,22);if(!vm)return 0;t.handles[262+row]=vm->id;}results_creation_first=anm_creation_count();(void)first;}
    return 1;
}
API(records_probe_value) i32 records_probe_value(u32 field){auto& t=*session.title;switch(field){case 0:return i32(t.screen);case 1:return t.substate;case 2:return t.cursor.selected;case 3:return t.secondary.selected;case 4:return t.page.selected;case 5:return t.page.count;case 6:return t.record_rows;case 7:return t.unlock_progress;case 8:return t.unlock_timeout;case 9:return t.text_requests.size();case 10:return t.sounds.size();default:return -1;}}
API(records_probe_text) const char* records_probe_text(u32 row){return session.title->text_requests[row].bytes.c_str();}
API(records_probe_text_value) u32 records_probe_text_value(u32 row,u32 field){auto& t=*session.title;auto& r=t.text_requests[row];switch(field){case 0:return r.color;case 1:return r.offset;case 2:return r.font;case 3:return r.style;case 4:for(u32 n=0;n<10;++n)if(t.handles[262+n]==r.animation)return n;return 0xffffffff;default:return 0;}}
API(records_probe_sound) i32 records_probe_sound(u32 row){return session.title->sounds[row];}
API(records_probe_unlock) void records_probe_unlock(u32 progress,u32 timeout,i32 key){auto& t=*session.title;t.unlock_progress=progress;t.unlock_timeout=timeout;t.key_edges.fill(0);if(key>=0)t.key_edges[key]=128;
    constexpr u32 seen[]={0,99998,99999,0x7fffffff,0xffffffff},clear[]={0,0x7fffffff,0xffffffff};for(u32 id=0;id<120;++id)std::memcpy(session.scores.characters[6].data()+0x978+id*0x9c+0x88,&seen[id%5],4);for(u32 c=0;c<6;++c)std::memcpy(session.scores.characters[c].data()+0x7dc,&clear[c%3],4);
}
API(records_probe_scores) const u8* records_probe_scores(u32 c){return session.scores.characters[c].data();}
API(records_probe_settings) const u8* records_probe_settings(){return session.scores.settings.data();}
API(records_text_records) u8* records_text_records(){auto& t=*session.title;return session.scores.characters[t.cursor.selected].data()+0x10+t.secondary.selected*0x118;}
API(records_text_stats) void records_text_stats(u32 count,u32 time,u32 clears){auto& t=*session.title;auto* p=session.scores.characters[t.cursor.selected].data();std::memcpy(p+0x7b8,&count,4);std::memcpy(p+0x7bc,&time,4);std::memcpy(p+0x7c0+t.secondary.selected*4,&clears,4);}
API(records_text_queue) u32 records_text_queue(){results_text=std::make_unique<AsciiText>(session.resources.core.ascii);session.title->queue_ascii(*results_text);return results_text->requests.size();}
API(music_probe_setup) u32 music_probe_setup(u32 substate,u32 timer,u32 selected,u32 heard,u32 prompt,u32 line){
    results_probe_setup(0,1,0,13,substate,timer);auto& t=*session.title;t.text_resource=&session.resources.core.text;
    std::vector<u8> comments;if(!source.read("musiccmt.txt",comments)||!t.load_music_comments(comments.data(),u32(comments.size())))return 0;
    t.cursor.count=10;t.cursor.select(6);t.cursor.push();t.cursor.count=t.music_entries.size();t.cursor.select(selected);t.cursor.wrap=1;
    t.music_state={i32(t.music_entries.size()),i32(line),i32(selected),i32(prompt),i32(selected>9?selected-9:0)};
    for(u32 n=0;n<t.music_entries.size();++n)session.scores.settings[0x26+n]=heard;
    if(substate){for(u32 n=0;n<t.music_entries.size();++n){auto* vm=session.animations.create(session.resources.core.title,171+n,24,22);if(!vm)return 0;vm->script_position={};t.handles[278+n]=vm->id;}for(u32 n=0;n<8;++n){auto* vm=session.animations.create(session.resources.core.text,19+n,0,22);if(!vm)return 0;t.handles[298+n]=vm->id;}}
    results_creation_first=anm_creation_count();return 1;
}
API(music_probe_value) i32 music_probe_value(u32 field){auto& t=*session.title;switch(field){case 0:return i32(t.screen);case 1:return t.substate;case 2:return t.cursor.selected;case 3:return t.music_state.count;case 4:return t.music_state.line;case 5:return t.music_state.selected;case 6:return t.music_state.prompt;case 7:return t.music_state.scroll;case 8:return t.cursor.depth;case 9:return t.music_request;case 10:return t.music_pause;default:return -1;}}
API(music_probe_position) u32 music_probe_position(u32 row,u32 field){auto& t=*session.title;auto* vm=session.animations.find(t.handles[278+row]);if(!vm)return 0xffffffff;const auto& p=vm->position_interpolation;switch(field){case 0:return float_bits(p.end[0]);case 1:return float_bits(p.end[1]);case 2:return float_bits(p.end[2]);case 3:return p.duration;case 4:return u32(p.mode);default:return 0;}}
API(replay_menu_setup) u32 replay_menu_setup(u32 substate,u32 timer,u32 selected,u32 page,u32 mask,u32 spell,u32 flags,u32 last,u32 background){
    results_probe_setup(0,1,0,11,substate,timer);auto& t=*session.title;t.flags=flags;t.cursor.count=10;t.cursor.select(4);t.cursor.push();t.cursor.count=25;t.cursor.select(17);if(substate==4)t.cursor.push();t.cursor.count=substate==4?7:25;t.cursor.select(selected);t.cursor.wrap=1;
    t.page.count=3;t.page.wrap=1;t.page.select(page);t.replay_file=page*25+17;t.replay_stage=3;t.last_replay=last;
    if(mask){auto entry=std::make_shared<TitleMenu::ReplayEntry>();entry->path="th14_01.rpy";ReplayRecorder writer;if(!writer.begin(0,0,0,false,0))return 0;writer.header[10]=spell;const u32 spell_id=1;std::memcpy(writer.header.data()+0x90,&spell_id,4);ReplayStageState state{};
        for(u32 n=1;n<=7;++n)if(mask&(1u<<(n-1))){if(!writer.start_stage(n,state,true)||!writer.tick(0,0,0)||!writer.finish_stage())return 0;}
        if(!writer.save("REPLAY",0,7,0,0,entry->file)||!entry->replay.open(entry->file.data(),u32(entry->file.size())))return 0;t.replay_files.fill(entry);
    }
    if(background){auto* vm=session.animations.create(session.resources.core.title,86,24,22);if(!vm)return 0;t.handles[86]=vm->id;}
    results_creation_first=anm_creation_count();return 1;
}
API(replay_menu_value) i32 replay_menu_value(u32 field){auto& t=*session.title;switch(field){case 0:return i32(t.screen);case 1:return t.substate;case 2:return t.cursor.selected;case 3:return t.cursor.count;case 4:return t.page.selected;case 5:return t.cursor.depth;case 6:return t.cursor.disabled_count;case 7:return t.flags;case 8:return t.replay_file;case 9:return t.replay_stage;case 10:return t.last_replay;case 11:return t.replay_start_requested;case 12:return t.replay_scan_requested;case 13:return t.fade_requested;case 14:return t.music_fade;default:return -1;}}
API(replay_text_setup) u32 replay_text_setup(u32 substate,u32 timer,float fraction,u32 selected,u32 page,u32 file){results_probe_setup(0,1,0,11,substate,timer);auto& t=*session.title;t.timer.fractional=fraction;t.cursor.count=substate==4?7:25;t.cursor.select(selected);t.page.select(page);t.replay_file=file;return 1;}
API(replay_text_entry) u32 replay_text_entry(u32 index,const u8* header,u32 mask,const u8* stage_headers){
    if(index>=75)return 0;auto& t=*session.title;if(!header){t.replay_files[index].reset();return 1;}
    ReplayRecorder writer;if(!writer.begin(0,0,0,false,0))return 0;std::memcpy(writer.header.data(),header,writer.header.size());ReplayStageState state{};
    for(u32 n=1;n<=7;++n)if(mask&(1u<<(n-1))){if(!writer.start_stage(n,state,true))return 0;std::memcpy(writer.stages[n].header.data(),stage_headers+(n-1)*kReplayStageHeader,kReplayStageHeader);if(!writer.tick(0,0,0)||!writer.finish_stage())return 0;}
    auto entry=std::make_shared<TitleMenu::ReplayEntry>();entry->path="th14_udABCD.rpy";u32 score,reach,continues;float slowdown;std::memcpy(&score,header+0x14,4);std::memcpy(&reach,header+0x88,4);std::memcpy(&continues,header+0x8c,4);std::memcpy(&slowdown,header+0x74,4);
    if(!writer.save(reinterpret_cast<const char*>(header),signed_bits(score),signed_bits(reach),signed_bits(continues),slowdown,entry->file)||!entry->replay.open(entry->file.data(),u32(entry->file.size())))return 0;t.replay_files[index]=entry;return 1;
}
API(replay_text_queue) u32 replay_text_queue(){results_text=std::make_unique<AsciiText>(session.resources.core.ascii);session.title->queue_ascii(*results_text);return results_text->requests.size();}
API(practice_probe_setup) u32 practice_probe_setup(u32 selection,u32 difficulty,u32 substate,u32 timer,u32 selected,u32 mask,u32 last,u32 numbers){
    results_probe_setup(selection,difficulty,0,8,substate,timer);auto& t=*session.title;t.selection.flags=16;t.selection.last_practice=last;t.selection.practice_start=4;t.number_keys=numbers;t.cursor.count=2;t.cursor.select(1);t.cursor.push();t.cursor.count=6;t.cursor.wrap=1;t.cursor.select(selected);
    auto* p=session.scores.characters[selection].data();for(u32 n=0;n<6;++n){const u32 index=n+1+difficulty*8,score[]={0,2345678,0x7fffffff,0x80000000};p[ScoreFile::practice_flags_offset+1+index*8]=(mask>>n)&1;const u32 value=score[n%4];std::memcpy(p+ScoreFile::practice_score_offset+index*8,&value,4);}return 1;
}
API(practice_probe_value) i32 practice_probe_value(u32 field){auto& t=*session.title;switch(field){case 0:return i32(t.screen);case 1:return t.substate;case 2:return t.cursor.selected;case 3:return t.cursor.count;case 4:return t.cursor.depth;case 5:return t.selection.last_practice;case 6:return t.selection.practice_start;case 7:return t.selection.stage;case 8:return t.start_requested;case 9:return t.fade_requested;case 10:return t.music_fade;default:return -1;}}
API(spell_stage_setup) u32 spell_stage_setup(u32 substate,u32 timer,u32 stage,u32 loadout,i32 resume,u32 background){
    results_probe_setup(loadout,1,0,17,substate,timer);auto& t=*session.title;t.selection.flags=32;t.selection.last_practice=2;t.selection.resume_spell_stage=resume;t.cursor.count=10;t.cursor.select(3);t.cursor.push();t.cursor.count=7;t.cursor.select(stage);t.cursor.wrap=1;t.secondary.count=6;t.secondary.wrap=1;t.secondary.select(loadout);
    if(background){for(u32 script:{198u,259u}){auto* vm=session.animations.create(session.resources.core.title,script,24,22);if(!vm)return 0;t.handles[script]=vm->id;}auto* vm=session.animations.create(session.resources.core.ascii,19,2,22);if(!vm)return 0;t.handles[261]=vm->id;}
    results_creation_first=anm_creation_count();return 1;
}
API(spell_stage_value) i32 spell_stage_value(u32 field){auto& t=*session.title;switch(field){case 0:return i32(t.screen);case 1:return t.substate;case 2:return t.cursor.selected;case 3:return t.cursor.count;case 4:return t.cursor.depth;case 5:return t.secondary.selected;case 6:return t.selection.spell_stage;case 7:return t.selection.last_practice;case 8:return t.selection.resume_spell_stage;default:return -1;}}
API(spell_select_setup) u32 spell_select_setup(u32 screen,u32 substate,u32 timer,u32 stage,u32 row,u32 selected,u32 loadout,u32 mode,i32 resume){
    if(!spell_stage_setup(2,17,stage,loadout,-1,1))return 0;auto& t=*session.title;t.text_resource=&session.resources.core.text;t.selection.spell_stage=stage;t.selection.spell_row=row;
    for(auto& record:session.scores.characters)record.fill(0);
    for(u32 c=0;c<7;++c)for(u32 id=0;id<120;++id){auto* p=session.scores.characters[c].data()+ScoreFile::spell_offset+id*ScoreFile::spell_stride;std::snprintf(reinterpret_cast<char*>(p),128,"Spell %03u\x81\x48",id);
        const u32 score[]={0,2345678,0x7fffffff,0x80000000},words[]={id%3,(id+c)%3,mode==1||mode==2&&id%2?7u:0u,mode==3?5u:9u,0,0,score[id%4]};std::memcpy(p+0x80,words,sizeof(words));}
    t.cursor.push();t.cursor.count=stage==0?3:stage==1||stage==2?4:stage==3||stage==5?6:stage==4?5:12;t.cursor.select(row);t.screen=TitleScreen::SpellRecords;t.substate=0;
    if(screen==19||substate){if(!t.update(0,0))return 0;if(screen==19){t.cursor.push();t.cursor.count=5;t.cursor.disabled_count=0;if(substate)for(u32 n=0;n<5;++n)if(t.spell_choices[n]<0)t.cursor.disabled[t.cursor.disabled_count++]=n;}}
    t.screen=TitleScreen(screen);t.substate=substate;t.timer.set(i32(timer),&session.animations.rate);t.cursor.select(selected);t.selection.resume_spell_row=screen==18?resume:-1;t.selection.resume_spell_difficulty=screen==19?resume:-1;t.text_requests.clear();t.sounds.clear();results_creation_first=anm_creation_count();return 1;
}
API(spell_select_value) i32 spell_select_value(u32 field){auto& t=*session.title;switch(field){case 0:return i32(t.screen);case 1:return t.substate;case 2:return t.cursor.selected;case 3:return t.cursor.count;case 4:return t.cursor.depth;case 5:return t.secondary.selected;case 6:return t.selection.spell_stage;case 7:return t.selection.spell_row;case 8:return t.selection.resume_spell_row;case 9:return t.selection.resume_spell_difficulty;case 10:return t.cursor.disabled_count;case 11:return t.start_requested;case 12:return t.selection.spell_id;default:return -1;}}
API(spell_select_choice) i32 spell_select_choice(u32 n){return session.title->spell_choices[n];}
API(spell_launch_value) i32 spell_launch_value(u32 field){auto& t=*session.title;switch(field){case 0:return t.selection.spell_id;case 1:return t.selection.stage;case 2:return t.selection.character;case 3:return t.selection.partner;case 4:return t.selection.difficulty;case 5:return t.selection.resume_spell_stage;case 6:return t.selection.resume_spell_row;case 7:return t.selection.resume_spell_difficulty;case 8:return t.fade_requested;case 9:return t.music_fade;default:return -1;}}
API(spell_select_text_value) u32 spell_select_text_value(u32 row,u32 field){auto& r=session.title->text_requests[row];switch(field){case 0:return r.color;case 1:return r.offset;case 2:return r.font;case 3:return r.style;case 4:{auto* vm=session.animations.find(r.animation);return vm?u32(vm->script_index-193):0xffffffff;}default:return 0;}}
API(spell_session_begin) u32 spell_session_begin(u32 stage,i32 id,u32 selection,u32 difficulty){session.menu_selection.flags=32;session.menu_selection.spell_id=id;session.title.reset();return session.begin(source,stage,selection>>1,selection&1,difficulty);}
API(spell_session_value) i32 spell_session_value(u32 field){auto& s=session;switch(field){case 0:return s.state.spell_practice_id;case 1:return s.economy.lives;case 2:return s.economy.th14_bombs;case 3:return s.economy.power;case 4:return s.battle?s.battle->enemy_environment.spell_practice_id:-1;case 5:return s.battle?s.battle->enemy_commands.th14_run_flags:-1;case 6:return s.recording.header[10];case 7:return s.battle?s.battle->spells.run_flags:-1;case 8:return s.battle?s.battle->spell_id:-1;case 9:return s.battle?s.battle->spell_flags:-1;default:return -1;}}
API(archive_spell_source) const u8* archive_spell_source(u32 stage){static std::vector<u8> file;const std::string name="st0"+std::to_string(stage)+".ecl";return source.read(name.c_str(),file)?file.data():nullptr;}
API(archive_spell_size) u32 archive_spell_size(u32 stage){std::vector<u8> file;const std::string name="st0"+std::to_string(stage)+".ecl";return source.read(name.c_str(),file)?file.size():0;}
static EnemyState spell_interrupt_enemy;
API(spell_interrupt_run) i32 spell_interrupt_run(u32 flags,u32 boss,u32 slot,i32 health,i32 time){
    spell_interrupt_enemy={};spell_interrupt_enemy.flags=boss?0x800000:0;spell_interrupt_enemy.interrupts[slot]={100,200,"old_health","old_timeout"};
    EnemyEnvironment environment;EnemyGlobals globals(spell_interrupt_enemy,environment);EnemyCommandEnvironment commands;commands.th14_run_flags=flags;
    alignas(4) u8 data[48]{};auto* instruction=reinterpret_cast<EclInstruction*>(data);instruction->opcode=514;instruction->length=48;const i32 args[]={i32(slot),health,time};std::memcpy(data+16,args,sizeof(args));std::memcpy(data+32,"next_phase",11);EclContext context;context.instruction=instruction;
    const i32 result=enemy_th14_state_command(spell_interrupt_enemy,context,globals,commands);auto& r=spell_interrupt_enemy.interrupts[slot];if(r.health_script==reinterpret_cast<char*>(data+32))r.health_script="next_phase";if(r.timeout_script==reinterpret_cast<char*>(data+32))r.timeout_script="next_phase";return result;
}
API(spell_interrupt_word) i32 spell_interrupt_word(u32 slot,u32 field){const auto& r=spell_interrupt_enemy.interrupts[slot];return field?r.time:r.health;}
API(spell_interrupt_name) const char* spell_interrupt_name(u32 slot,u32 field){const auto& r=spell_interrupt_enemy.interrupts[slot];return field?r.timeout_script:r.health_script;}
static Dialogue* music_retained_dialogue=nullptr;
API(music_request_begin) u32 music_request_begin(u32 stage){session.resources.effects=nullptr;session.menu_selection.flags=0;session.title.reset();if(!session.begin(source,stage,0,0,1))return 0;music_retained_dialogue=session.battle->dialogue.get();return 1;}
API(music_request_run) u32 music_request_run(i32 id,u32 replay,u32 stop,u32 match){
    auto& b=*session.battle;b.events.clear();session.scores.settings.fill(0);b.enemy_commands.th14_run_flags=match?32:0;b.replaying=replay;b.th14_audio_flags=stop<<4;b.th14_current_music=match==1?stage_music(session.state.stage,id==-1):-1;results_creation_first=anm_creation_count();return b.start_dialogue(id);
}
API(music_request_value) i32 music_request_value(u32 field){auto& b=*session.battle;switch(field){case 0:return b.events.size();case 1:return anm_creation_count()-results_creation_first;case 2:return b.dialogue.get()==music_retained_dialogue;default:return -1;}}
API(music_request_event) i32 music_request_event(u32 n,u32 field){const auto& e=session.battle->events[n];if(field)return e.kind==BattleEventKind::BossMusic?1:0;return e.kind==BattleEventKind::MusicStop?4:e.kind==BattleEventKind::StageMusic||e.kind==BattleEventKind::BossMusic?2:-1;}
API(music_request_unlocks) const u8* music_request_unlocks(){return session.scores.settings.data()+0x26;}
API(music_result_request) i32 music_result_request(u32 flags){auto& b=*session.battle;b.spell_flags=flags;b.enemy_commands.th14_run_flags=32;b.game_over_requested=false;b.th14_spell_result_requested=false;b.replaying=false;if(!b.start_dialogue(-2))return -1;return b.game_over_requested?1:b.th14_spell_result_requested?2:0;}
static std::unique_ptr<PauseMenu> spell_end_menu;
API(spell_end_setup) u32 spell_end_setup(u32 completed,i32 state,i32 timer,i32 selected){
    session.animations.clear();for(auto& r:session.scores.characters)r.fill(0);session.scores.settings.fill(0);auto& core=session.resources.core;
    spell_end_menu=std::make_unique<PauseMenu>(session.animations,core.text,core.front,session.scores);auto& m=*spell_end_menu;m.spell_practice_id=26;m.selection=0;m.difficulty=2;m.stage=3;m.result_score=12345;
    if(!m.begin_end(true,completed))return 0;if(state!=21){m.timer.set(10,&session.animations.rate);if(!m.update(0,0))return 0;}
    m.state=state;m.timer.set(timer,&session.animations.rate);m.cursor.count=3;m.cursor.selected=m.cursor.previous=selected;m.sounds.clear();results_creation_first=anm_creation_count();return 1;
}
API(spell_end_tick) u32 spell_end_tick(u32 pressed,u32 repeat){return spell_end_menu->update(pressed,repeat);}
API(spell_end_value) i32 spell_end_value(u32 field){auto& m=*spell_end_menu;switch(field){case 0:return m.state;case 1:return m.cursor.selected;case 2:return m.cursor.previous;case 3:return m.cursor.count;case 4:return m.cursor.depth;case 5:return m.cursor.disabled_count;case 6:return m.timer.current;case 7:return m.sounds.size();case 8:return anm_creation_count()-results_creation_first;case 9:return i32(m.action);case 10:for(const auto& r:session.scores.characters)for(u8 b:r)if(b)return 1;return 0;case 11:return m.capture_requested;default:return -1;}}
API(spell_end_sound) i32 spell_end_sound(u32 n){return spell_end_menu->sounds[n];}
API(spell_session_pause) u32 spell_session_pause(){return session.pause();}
API(spell_session_end_value) i32 spell_session_end_value(u32 field){auto* m=session.pause_menu.get();if(!m)return -1;switch(field){case 0:return m->state;case 1:return m->cursor.selected;case 2:return m->capture_requested;case 3:return m->spell_practice_id;case 4:return m->completed;case 5:return m->sounds.size();default:return -1;}}
API(spell_session_result) u32 spell_session_result(u32 flags){session.battle->spell_flags=flags;return session.battle->start_dialogue(-2);}
API(spell_session_save) u32 spell_session_save(){return session.save_replay("SPELL",saved_replay,true);}
API(spell_session_replay) u32 spell_session_replay(){return session.begin_replay(source,saved_replay.data(),saved_replay.size());}
API(spell_session_replay_value) i32 spell_session_replay_value(u32 field){const auto& r=session.playback;switch(field){case 0:return r.decoded()[10];case 1:{i32 id;std::memcpy(&id,r.decoded().data()+0x90,4);return id;}case 2:return session.battle?session.battle->replay_entry.th14_practice_mode:-1;default:return -1;}}
static const AnmResource& startup_resource(u32 file){return file==2?session.resources.core.ascii:file==1?session.resources.core.title_variant:session.resources.core.title;}
API(startup_script) const u8* startup_script(u32 file,u32 index){const auto& f=startup_resource(file);return index<f.scripts.size()?f.scripts[index].bytes.data():nullptr;}
API(startup_script_size) u32 startup_script_size(u32 file,u32 index){const auto& f=startup_resource(file);return index<f.scripts.size()?f.scripts[index].bytes.size():0;}
API(startup_creation_count) u32 startup_creation_count(){return anm_creation_count();}
API(startup_creation_value) i32 startup_creation_value(u32 index,u32 field){return anm_creation_value(index,field);}
API(startup_state) u32 startup_state(u32 field){switch(field){case 0:return session.animations.active_count();case 1:return session.title?session.title->substate:0;case 2:return session.title?session.title->timer.current:0;case 3:return session.animations.visual_rng.calls;default:return 0;}}

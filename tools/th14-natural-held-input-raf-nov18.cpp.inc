
// PRIVATE NATURAL GAMEPLAY ACCEPTANCE: inputs and read-only observation only.
namespace th14_natural_acceptance {
using namespace th11;
Replay keys;bool enabled=false,armed=false;u32 reads=0,tails=0,last_stage=0,last_frame=0,last_key=0,callbacks=0,visited=0,first_seed=0,first_calls=0;
std::array<u32,8> stage_seeds{},stage_calls{};
void observe(const GameBattle& b){
 ++callbacks;const u32 stage=u32(b.resources.stage_number);if(stage<8&&!(visited&(1u<<stage))){stage_seeds[stage]=b.animations.script_rng.seed_value();stage_calls[stage]=b.animations.script_rng.call_count();}
 visited|=1u<<stage;if(callbacks==1){first_seed=b.animations.script_rng.seed_value();first_calls=b.animations.script_rng.call_count();}
}
u32 held(u32 menu){
 const auto& s=th11::sdl::app.session;
 if(!enabled||(s.state.phase!=GameSessionPhase::stage&&s.state.phase!=GameSessionPhase::loading)||s.state.replay||s.state.demo)return menu;
 u32 stage=s.recording.selected?s.recording.selected:s.state.stage;const auto* entry=keys.stage(stage);if(!entry||stage>=s.recording.stages.size())return menu;
 u32 frame=s.recording.selected==stage?s.recording.stages[stage].frames:0;
 if(stage!=s.state.stage&&frame>=entry->frames){if(const auto* incoming=keys.stage(s.state.stage)){stage=s.state.stage;entry=incoming;frame=0;}}
 last_stage=stage;last_frame=frame;++reads;u32 result=1;
 if(frame<entry->frames){const auto* p=keys.decoded().data()+entry->offset+kReplayStageHeader+frame*6;const bool terminal=p[0]==255&&p[1]==255&&p[2]==255&&p[3]==255&&p[4]==255&&p[5]==255;if(!terminal)result=u32(p[0])|u32(p[1])<<8;else ++tails;}else ++tails;
 last_key=result;return result;
}
}
extern "C" EMSCRIPTEN_KEEPALIVE int th14_acceptance_load_keys(const th11::u8* bytes,unsigned size){
 using namespace th14_natural_acceptance;auto& s=th11::sdl::app.session;if(armed||s.state.phase!=GameSessionPhase::title)return 0;
 if(!keys.open(bytes,size)||keys.character()!=0||keys.subtype()!=1||keys.difficulty()!=1||keys.stage_count()!=6||keys.uses_touch()||(keys.decoded()[10]&3))return 0;
 enabled=true;armed=true;auto previous=s.animations.before_initial_update;s.animations.before_initial_update=[previous](const th11::AnmVm& vm){auto& s=th11::sdl::app.session;if(!th11::StageCppWorkerScopeTh14::owns(&s)&&s.battle)s.battle->before_player_update=th14_natural_acceptance::observe;return !previous||previous(vm);};return 1;
}
extern "C" EMSCRIPTEN_KEEPALIVE unsigned th14_acceptance_natural_state(unsigned q){
 using namespace th14_natural_acceptance;const auto& a=th11::sdl::app;const auto& s=a.session;const auto* b=s.battle.get();const auto* e=s.ending.get();
 switch(q){case 0:return unsigned(s.state.phase);case 1:return s.state.stage;case 2:return s.recording.selected;case 3:return s.recording.selected<s.recording.stages.size()?s.recording.stages[s.recording.selected].frames:0;case 4:return b&&b->stage_active;case 5:return b&&b->pending_stage;case 6:return b?b->resources.stage_number:0;case 7:return callbacks;case 8:return first_seed;case 9:return first_calls;case 10:return s.economy.score_units;case 11:return s.economy.graze;case 12:return s.economy.lives;case 13:return e&&e->message=="staff.msg";case 14:return e?e->index:~0u;case 15:return e?e->frames:0;case 16:return e?e->seen:0;case 17:return visited;case 18:return !a.error.empty();case 19:return s.title?unsigned(s.title->screen):~0u;case 20:return s.title?s.title->substate:~0u;case 21:return s.title?s.title->cursor.selected:~0u;case 24:return s.practice_tools;case 25:return s.state.replay;case 26:return s.state.demo;case 27:return s.state.practice;case 28:return reads;case 29:return tails;case 30:return a.initial_ticks;case 31:return s.animations.script_rng.seed_value();case 32:return s.animations.script_rng.call_count();case 33:{unsigned n=0;if(e)for(auto id:e->images)n+=id!=0;return n;}case 34:return e&&e->active;case 35:return e&&e->resource_loading();case 36:return last_stage;case 37:return last_frame;case 38:return last_key;default:return ~0u;}
}

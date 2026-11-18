
// PRIVATE ACCEPTANCE EXPORTS. No production behavior changes outside explicit test calls.
extern "C" EMSCRIPTEN_KEEPALIVE int th14_acceptance_complete_boundary(){
 auto& s=th11::sdl::app.session;auto* b=s.battle.get();
 if(s.state.phase!=th11::GameSessionPhase::stage||s.state.replay||s.state.demo||s.state.practice||s.practice_tools)return -1;
 if(!b||!b->stage_active||b->pending_stage||b->resources.stage_number!=int(s.state.stage)||s.recording.selected!=s.state.stage)return 0;
 return b->dialogue_stage_complete()?1:-2;
}
extern "C" EMSCRIPTEN_KEEPALIVE int th14_acceptance_flow(unsigned q){
 const auto& s=th11::sdl::app.session;const auto* b=s.battle.get();const auto* e=s.ending.get();
 switch(q){case 0:return int(s.state.phase);case 1:return s.state.stage;case 2:return b&&b->stage_active;case 3:return b&&b->pending_stage;
 case 4:return b?b->resources.stage_number:0;case 5:return e?e->index:-1;case 6:return e&&e->active;case 7:return e&&e->resource_loading();
 case 8:return s.title?int(s.title->screen):-1;case 9:return s.state.character;case 10:return s.state.subtype;case 11:return s.state.difficulty;
 case 12:return e?e->flags:0;case 13:return e?e->line:0;case 14:return e?e->frames:0;case 15:return s.recording.selected;
 case 16:return s.state.demo;case 17:return s.state.replay;case 18:return s.state.practice;case 19:return s.practice_tools;
 case 20:return e?e->seen:0;case 21:return s.title?s.title->substate:-1;case 22:return s.title?s.title->cursor.selected:-1;
 case 23:{int n=0;if(e)for(auto id:e->images)n+=id!=0;return n;}case 25:return e&&e->message=="staff.msg";default:return -1;}
}

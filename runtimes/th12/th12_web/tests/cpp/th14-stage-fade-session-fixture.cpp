#include "th14-session-fixture.cpp"
static bool was_paused=false;
API(fade_session_begin) u32 fade_session_begin(u32 kind,float rate){
 if(!session.begin(source,1,0,0,1)||!session.battle||!session.battle->stage)return 0;
 renderer.invalidate();session.animations.rate=rate;session.battle->enemy_environment.rate=rate;session.battle->fades.effects.clear();was_paused=false;
 if(kind==2)session.battle->stage->fade_out(session.battle->fades);else session.battle->stage->resume_background();
 if(!draw())return 0;
 // resume_background starts a60-tick overlap. Let the actual foreground
 // countdown reach the native type3 creation boundary through normal frames.
 for(u32 frame=0;kind==3&&session.battle->fades.effects.empty()&&frame<1000;++frame)if(!session.update({})||!draw())return 0;
 return session.battle->fades.effects.size();
}
API(fade_session_tick) u32 fade_session_tick(u32 paused){
 if(paused&&!was_paused){if(!session.pause())return 0;}else if(!paused&&was_paused){if(!session.resume())return 0;}was_paused=paused;
 if(!session.update({})||!draw())return 0;return 1;
}
API(fade_session_count) u32 fade_session_count(){return session.battle->fades.effects.size();}
API(fade_session_field) u32 fade_session_field(u32 i){const auto& e=session.battle->fades.effects[i/8];u32 fractional;std::memcpy(&fractional,&e.timer.fractional,4);u32 fields[]={u32(e.type),u32(e.duration),u32(e.alpha),e.color,e.priority,u32(e.timer.previous),u32(e.timer.current),fractional};return fields[i%8];}

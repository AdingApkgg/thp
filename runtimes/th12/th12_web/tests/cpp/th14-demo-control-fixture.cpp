#include "th14-replay-session-fixture.cpp"
API(begin_interactive_demo) i32 begin_interactive_demo(u32 index){session.interactive=true;return begin_demo(index);}
API(demo_fade) i32 demo_fade(u32 n){
 if(!session.battle)return -1;
 for(const auto& f:session.battle->fades.effects)if(f.type==5){
  const i32 v[]={f.type,f.duration,i32(f.color),i32(f.priority),f.timer.current,f.alpha};
  return n<6?v[n]:-1;
 }
 return -1;
}
API(control_tick) i32 control_tick(u32 held,i32 pause){return session.update({held,0,0,bool(pause)});}
API(stage_frame) u32 stage_frame(){return session.state.frame;}
API(demo_flag) i32 demo_flag(){return session.state.demo;}
// Only the controller decision clock is selected for local native rows.
// Complete unmodified replay timelines are exercised separately.
API(control_frame) void control_frame(u32 frame){session.state.frame=frame;}
API(fade_draw_count) u32 fade_draw_count(u32 alpha,u32 target){
 u32 count=0;
 for(const auto& s:graphics.submissions){
  if(s.target!=target||s.stride!=20||s.size!=80)continue;
  bool equal=true;
  for(u32 n=0;n<4;++n){
   const auto* p=graphics.data.data()+s.start+n*20;float xyz[4];u32 color;
   std::memcpy(xyz,p,16);std::memcpy(&color,p+16,4);
   if(xyz[0]!=(n&1?640.f:0.f)||xyz[1]!=(n&2?480.f:0.f)||xyz[2]!=0||xyz[3]!=1||color!=(alpha<<24))equal=false;
  }
  if(equal)++count;
 }
 return count;
}
API(title_fade) void title_fade(){session.title_fades.start(5,60,0,61,&session.animations.rate);}
API(existing_priority_fade) void existing_priority_fade(){session.battle->fades.start(5,60,0,67,&session.animations.rate);}

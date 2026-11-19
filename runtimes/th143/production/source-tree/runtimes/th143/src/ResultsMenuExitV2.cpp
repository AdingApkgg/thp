#include "ResultsMenuExitV2.hpp"
#include <cstdio>
#include "CheatAnimation.hpp"
#include "AnmSignal.hpp"
namespace th143 {
namespace {
bool tick(AnmView t,AnmWorld& w){const u32 old=t.get(4),token=t.get(12);float rate=1;if(token&&!w.timer_rate(token,rate))return false;t.put(0,old);const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=t.floating(8)+(unit?1.f:rate);t.put(8,word(value));t.put(4,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);return true;}
}
i32 results_menu_exit_frame_v2(PauseMenu& menu,SaveData& save,GameOverGlobals& g,ResultsMenuIdleInput& k,AnmWorld& w,AnmOverlay& overlay,AnmView hud,ResultsMenuExitHost& host,AnmView game,u32& scene,const std::array<u32,10>& day_first,PauseReplayPageHost& replay){
 auto m=menu.view();w.rate=g.rate;if(m.get(0x3e4)>3)return tick(m.sub(0x10),w)&&tick(m.sub(0x24),w)?1:-2;if(m.get(0x3e4)!=3)return -2;
 auto signal=[&](u32 at,i32 id){return signal_animation(w,m.get(at),id);};auto cursor=MenuCursor{m.sub(0x38)};
 const u32 sub=m.get(0x3ec);
 if(sub==7){
  if(signed_word(m.get(0x14))>=10){u32 result=0;if(!replay.pause_replay_select(6,result))return -2;
   if(result==1)menu.substate(8,w.global_rate_token());
   else if(result==2){if(!signal(0x91b8,8))return -2;menu.substate(1,w.global_rate_token());}
  }
 }else if(sub==8){
  if(signed_word(m.get(0x14))>=10&&!replay.pause_replay_name(7))return -2;
 }else if(sub==0&&signed_word(m.get(0x14))>=10){
  if(k.scene>=SaveData::scene_count)return -2;hud.put(0x144,k.score);if(k.high_score<k.score)k.high_score=k.score;
  const u32 at=k.scene*SaveData::scene_size+0x70;if(k.score>save.view().get(at))save.view().put(at,k.score);m.put(0x1f8,1);
  u32 handle;if(!overlay.create(w,m.get(0x91c0),109,nullptr,0,-1,4,handle))return -2;m.put(0x1e8,handle);menu.substate(1);m.put(0x40,6);m.put(0x108,1);
  if(signed_word(k.deaths)>0&&!cursor.disable(2))return -2;
  if(signed_word(k.within_day)>=signed_word(k.day_scene_count-1)){
   if(!cursor.disable(1))return -2;auto parent=w.find(m.get(0x1e8));if(!parent.data)m.put(0x1e8,0);auto child=find_animation_child(w,parent,137);if(!signal_animation(w,child.data?child.get(0x540):0,5,true))return -2;
  }
  if(!cursor.select(0)||!signal(0x1e8,3)||!signal(0x1e8,i32(std::int16_t(m.get(0x38)))+7))return -2;
 }else if(sub==1){
  if(k.message_owner||signed_word(save.view().get(0xf16c))>0)return -2;cursor.begin();i32 ignored;
  if(((k.fresh|k.repeated)&0x10)&&!cursor.move(-1,ignored))return -2;
  if(((k.fresh|k.repeated)&0x20)&&!cursor.move(1,ignored))return -2;
  if(m.get(0x3c)!=m.get(0x38)&&(!signal(0x1e8,i32(std::int16_t(m.get(0x38)))+7)||!host.menu_sound(10)))return -2;
  if(k.fresh&0x80001){
   const u32 choice=m.get(0x38);if(choice>3)return -2;
   auto parent=w.find(m.get(0x1e8));if(!parent.data)m.put(0x1e8,0);auto child=find_animation_child(w,parent,i32(choice+136));
   if(!signal_animation(w,child.data?child.get(0x540):0,6)||!host.menu_sound(7))return -2;
   menu.substate(2);hud.put(0x144,k.score);if(k.high_score<k.score)k.high_score=k.score;
   if(choice==0){menu.substate(2);if(!host.menu_sound(7))return -2;}
   if(choice==2){
    if(!signal(0x91b8,3))return -2;menu.substate(7,w.global_rate_token());u32 ignored=0;
    if(!replay.replay_menu_call(0x484730,menu.self+0x1e8,{},ignored)||!cursor.push())return -2;
    m.put(0x40,25);m.put(0x108,1);if(!cursor.select(0))return -2;
    for(u32 i=1;i<=25;++i){char filename[64];const i32 n=std::snprintf(filename,sizeof filename,"th143_%.2d.rpy",signed_word(i));u32 token;
     if(n<0||u32(n)>=sizeof filename||!replay.pause_replay_load(reinterpret_cast<const u8*>(filename),u32(n)+1,token))return -2;m.put(0x204+(i-1)*4,token);
    }
   }

  }
  if(k.fresh&0x102){if(!host.menu_sound(9))return -2;if(m.get(0x38)&&(!cursor.select(0)||!signal(0x1e8,i32(std::int16_t(m.get(0x38)))+7)))return -2;}
 }else if(sub==2){
  const u32 choice=m.get(0x38),time=m.get(0x14);if(choice!=0&&choice!=1&&choice!=3)return -2;
  if(time==2&&choice==0&&!host.results_exit_fade())return -2;
  if(signed_word(time)>=(choice==0?38:12)){
   double now;if(!g.clock.sample(host,now))return -2;g.statistics_time=now;
   if(!signal(0x1ec,1)||!signal(0x1e8,1))return -2;g.rate=m.floating(0x2d8);w.rate=g.rate;m.put(0x3e4,4);
   if(choice==0)g.application_state=(g.config&0x2000)?2:4;
   else if(choice==3)g.application_state=10;
   else {if(k.day>=10||!game.data)return -2;const u32 within=game.get(0x2c)+1;game.put(0,0);game.put(0x2c,within);game.put(0x48,within);scene=day_first[k.day]+within;game.put(4,0);game.put(12,0);game.put(0x1c,0xffffffff);g.game_flags&=~0x60u;g.application_state=19;}
  }
 }else if(sub!=0)return -2;
 return tick(m.sub(0x10),w)&&tick(m.sub(0x24),w)?1:-2;
}
}

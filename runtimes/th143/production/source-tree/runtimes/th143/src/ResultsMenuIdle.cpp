#include "ResultsMenuIdle.hpp"
#include "CheatAnimation.hpp"
#include "AnmSignal.hpp"
namespace th143 {
namespace {
bool tick(AnmView t,AnmWorld& w){const u32 old=t.get(4),token=t.get(12);float rate=1;if(token&&!w.timer_rate(token,rate))return false;t.put(0,old);const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=t.floating(8)+(unit?1.f:rate);t.put(8,word(value));t.put(4,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);return true;}
}
i32 results_menu_idle_frame(PauseMenu& menu,SaveData& save,GameOverGlobals& g,ResultsMenuIdleInput& k,AnmWorld& w,AnmOverlay& overlay,AnmView hud,FailureMenuHost& host){
 auto m=menu.view();if(m.get(0x3e4)!=3)return -2;w.rate=g.rate;
 auto signal=[&](u32 at,i32 id){return signal_animation(w,m.get(at),id);};auto cursor=MenuCursor{m.sub(0x38)};
 const u32 sub=m.get(0x3ec);
 if(sub==0&&signed_word(m.get(0x14))>=10){
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
  if(k.fresh&0x80001)return -2;
  if(k.fresh&0x102){if(!host.menu_sound(9))return -2;if(m.get(0x38)&&(!cursor.select(0)||!signal(0x1e8,i32(std::int16_t(m.get(0x38)))+7)))return -2;}
 }else if(sub!=0)return -2;
 return tick(m.sub(0x10),w)&&tick(m.sub(0x24),w)?1:-2;
}
}

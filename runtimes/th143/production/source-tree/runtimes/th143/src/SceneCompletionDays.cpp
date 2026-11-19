#include "SceneCompletionDays.hpp"
namespace th143 {
namespace {
void increment(AnmView s,u32 at,i32 maximum){const u32 value=s.get(at);if(signed_word(value)<maximum)s.put(at,value+1);}
}
bool complete_scene(SaveData& save,SceneCompletionGlobals& g,SceneCompletionHost& host){
 if(g.scene>=SaveData::scene_count||g.day>=10||g.primary>=SaveData::item_count)return false;
 if((g.flags&0x60)!=0x40&&!host.clear_bonus(g.score))return false;
 if(!host.finish_player_shots()||(g.audio_active&&!host.stop_completion_audio()))return false;
 if(g.root_mode)return host.finish_replay();
 if(g.signals&&!host.capture_clear_preview(g.day,g.within_day))return false;
 auto s=save.view();const u32 base=8+g.scene*SaveData::scene_size;
 increment(s,0xf080,99999999);increment(s,0xef28,9999999);increment(s,base+0x38,9999999);
 if(!save.item_level(10,true,g.alternate,host))return false;
 if(g.day==9&&!host.achievement(9))return false;
 const u32 total=s.get(0xef2c);i32 milestone=-1;
 switch(total){case 5:milestone=1;break;case 10:milestone=2;break;case 20:milestone=3;break;case 30:milestone=4;break;case 40:milestone=5;break;case 50:milestone=6;break;case 60:milestone=7;break;default:if(signed_word(total)>=75)milestone=0;}
 if(milestone>=0&&!host.achievement(u32(milestone)))return false;
 const u32 item=SaveData::items+g.primary*SaveData::item_size;
 increment(s,item+0x14,9999999);increment(s,base+0x10+g.primary*4,9999999);
 if(!save.item_level(g.primary,true,g.alternate,host))return false;
 if(!g.equipment_used){
  increment(s,0xeef4,9999999);increment(s,base+0x34,9999999);
  if(!save.item_level(9,true,g.alternate,host)||!save.item_level(9,true,g.alternate,host))return false;
  const u32 unlocked=(u32(save.data[0xefac])+1)*3;if(unlocked>9)return false;
  for(u32 i=0;i<unlocked;++i)if(!s.get(base+0x10+i*4)){
   increment(s,SaveData::items+i*SaveData::item_size+0x14,9999999);increment(s,base+0x10+i*4,9999999);
   if(!save.item_level(i,true,g.alternate,host)||!save.item_level(i,true,g.alternate,host))return false;
  }
 }
 if(g.score>s.get(base+0x68))s.put(base+0x68,g.score);
 u32 cleared=0;for(u32 i=0;i<g.day_count[g.day];++i){const u32 scene=g.day_first[g.day]+i;if(scene>=SaveData::scene_count)return false;if(signed_word(s.get(scene*SaveData::scene_size+0x40))>0)++cleared;}
 if(cleared>=g.day_count[g.day]&&!host.achievement(g.day+20))return false;
 if(!(g.flags&0x400))return host.open_results_menu();
 if(g.day==0){if((g.flags&0x800)&&!host.achievement(10))return false;if(!host.open_completion_message(3))return false;save.data[0xefb8]=1;return true;}
 auto append=[&](u32 value){const u32 count=s.get(0xf16c);if(count>=(SaveData::bytes-0xf170)/4)return false;s.put(0xf170+count*4,value);s.put(0xf16c,count+1);return true;};
 if(g.day==2){if(!save.data[0xf088]){save.data[0xefac]=1;if(!append(6)||!append(4)||!append(5)||!host.achievement(11))return false;save.data[0xf088]=1;}return host.open_results_menu();}
 if(g.day==4){if(!save.data[0xf089]){save.data[0xefac]=2;if(!append(9)||!append(8)||!append(7)||!host.achievement(12))return false;save.data[0xf089]=1;}return host.open_results_menu();}
 if(g.day==5){if(!save.data[0xf08a]){if(!append(10)||!host.achievement(13))return false;save.data[0xf08a]=1;}return host.open_results_menu();}
 if(g.day==7){if(!host.achievement(8))return false;save.data[0xf08b]=1;return host.open_results_menu();}
 return true;
}
}

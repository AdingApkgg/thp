#include "../src/FailureManualPageV152.hpp"
// Original449c60 uses different substate numbers from4486c0 pause controls.
static bool campaign_failure_subpage_v152(PauseMenu& menu,u32 sub){
 auto m=menu.view();if(sub==11)return advance_failure_manual_page_v152(m,menu.self,campaign_manual_services);
 if(sub==10)return advance_results_equipment_page(menu,gameplay_pause_equipment);
 if(sub==7){
  if(!m.get(0x14)){
   for(u32 i=1;i<=25;++i){char filename[64];const i32 n=std::snprintf(filename,sizeof filename,"th143_%.2d.rpy",signed_word(i));u32 token;if(n<0||u32(n)>=sizeof filename||!campaign_replay_save_services.pause_replay_load(reinterpret_cast<const u8*>(filename),u32(n)+1,token))return false;m.put(0x204+(i-1)*4,token);}return true;
  }
  if(signed_word(m.get(0x14))<10)return true;u32 result;if(!campaign_replay_save_services.pause_replay_select(5,result))return false;
  if(result==1)menu.substate(8,world->global_rate_token());else if(result==2)menu.substate(1,world->global_rate_token());return true;
 }
 if(sub==8)return signed_word(m.get(0x14))<10||campaign_replay_save_services.pause_replay_name(7);
 return false;
}

struct CampaignSpecialMessageServices:HudSpecialMessageHost {
 u32 calls=0,last_id=0,last_service=0;
 bool special_message_read(u32 p,void* out,u32 n)override{
  if(n==4){u32 value;bool own=true;switch(p){
   case 0x4e47b0:value=title_root_game.game_flags;break;
   case 0x4e6a0c:value=title_root_aux->special_owner;break;
   case 0x4e6a5c:value=title_root_globals.root;break;
   case 0x4e6bac:value=title_scene_handoff_descriptor;break;
   case 0x4e6b9c:value=common_load_bindings->save_owner;break;
   default:own=false;
  }if(own){std::memcpy(out,&value,4);return true;}}
  return campaign_dialog_services.dialog_update_read(p,out,n);
 }
 bool special_message_write(u32 p,const void* bytes,u32 n)override{
  const u32 save=common_load_bindings->save_owner;if(p>=save&&std::uint64_t(p)+n<=std::uint64_t(save)+common_save->data.size()){std::memcpy(common_save->data.data()+p-save,bytes,n);return true;}
  return campaign_dialog_services.dialog_update_write(p,bytes,n);
 }
 AnmView special_message_audio()override{return {common_load_audio.data()};}
 bool special_message_game_over(u32 reason)override{last_service=0x449990;if(reason)return false;return title_failure_play_services.gameplay_game_over(false);}
 // Compatibility name in the frozen caller gate;433940 is scene completion.
 bool special_message_statistics_begin(u32 root)override{last_service=0x433940;return root==title_root_globals.root&&title_dodge_complete_scene();}
}campaign_special_message_services;
API(campaign_special_message_diagnostic) u32 campaign_special_message_diagnostic(u32 i){switch(i){case 0:return campaign_special_message_services.calls;case 1:return campaign_special_message_services.last_id;case 2:return campaign_special_message_services.last_service;default:return 0;}}

struct CampaignTitleNoticeServices:TitleSceneNoticeHost {
 bool timer_rate(u32 p,float& value)override{return world->timer_rate(p,value);}
 bool title_notice_create(u32 id)override{u32 owner;if(!day1_notice_results_services.results_create_notice(id,owner))return false;title_activation_globals.trophy_owner=owner;return true;}
 bool title_notice_destroy()override{if(!day1_notice_results_services.results_destroy_notice(day1_notice_globals.owner))return false;title_activation_globals.trophy_owner=0;return true;}
 bool title_notice_dialog(AnmView title)override{
  const u32 row=title.get(0xdff0);if(row<GameTitleRuntime::self||std::uint64_t(row)+0x20c>std::uint64_t(GameTitleRuntime::self)+GameTitleRuntime::bytes)return false;
  const auto text=title.sub(row-GameTitleRuntime::self);auto string=[&](u32 at){std::vector<u8> out;for(u32 i=0;i<256&&text.data[at+i];++i)out.push_back(text.data[at+i]);return out;};
  return show_title_dialog(*title_owner,*world,title_dialog_recorder,string(8),string(0x108),1080.f,320.f,text.floating(0x208));
 }
 bool title_notice_responses()override{return title_session_png&&title_session_saved&&consume_title_scene_responses(*title_owner,*world,*title_session_png,*title_session_saved);}
}campaign_title_notice_services;
static bool campaign_title_notice_gate(u32& result,bool& handled){
 title_activation_globals.trophy_owner=day1_notice_globals.owner;
 const bool ok=advance_title_scene_notice(title_owner->view(),common_save->view(),day1_notice_view(),day1_notice_globals.owner,campaign_title_notice_services,handled,result);
 title_activation_globals.trophy_owner=day1_notice_globals.owner;return ok;
}

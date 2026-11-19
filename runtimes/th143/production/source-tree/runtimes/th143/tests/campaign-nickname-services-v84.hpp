static std::array<u8,256> campaign_nickname_scratch{},campaign_nickname_current{},campaign_nickname_previous{};
static std::array<u8,0x108> campaign_nickname_raw{};
static std::vector<std::string> campaign_nickname_text;
static u32 campaign_nickname_failed=0,campaign_nickname_frames=0,campaign_nickname_draws=0,campaign_nickname_captures=0,campaign_nickname_created=0,campaign_nickname_destroyed=0,campaign_nickname_cells=0;
struct CampaignNicknameServices:CampaignOptionServices,TitleNicknameDrawHost {
 bool title_option_read(u32 p,void* out,u32 n)override{
  auto copy=[&](u32 base,const void* data,u32 size){if(p<base||std::uint64_t(p)+n>std::uint64_t(base)+size)return false;std::memcpy(out,static_cast<const u8*>(data)+p-base,n);return true;};
  if(copy(0x541360,campaign_nickname_scratch.data(),256)||copy(0x540e20,campaign_nickname_raw.data(),campaign_nickname_raw.size())||copy(0x541160,campaign_nickname_current.data(),256)||copy(0x541260,campaign_nickname_previous.data(),256)||copy(0x4e6b80,&day1_notice_globals.owner,4))return true;
  if(const auto* bytes=day1_notice_region(p,n)){std::memcpy(out,bytes,n);return true;}return CampaignOptionServices::title_option_read(p,out,n);
 }
 bool title_option_write(u32 p,const void* in,u32 n)override{
  auto copy=[&](u32 base,void* data,u32 size){if(p<base||std::uint64_t(p)+n>std::uint64_t(base)+size)return false;std::memcpy(static_cast<u8*>(data)+p-base,in,n);return true;};
  if(copy(0x541360,campaign_nickname_scratch.data(),256)||copy(0x540e20,campaign_nickname_raw.data(),campaign_nickname_raw.size())||copy(0x541160,campaign_nickname_current.data(),256)||copy(0x541260,campaign_nickname_previous.data(),256)||copy(GameAsciiRuntime::self,game_ascii->data.data(),game_ascii->data.size()))return true;
  return CampaignOptionServices::title_option_write(p,in,n);
 }
 bool name(u32 p,std::string& out){out.clear();for(u32 i=0;i<512;++i){u8 value;if(!title_option_read(p+i,&value,1))return false;if(!value)return true;out.push_back(char(value));}return false;}
 bool title_option_call(u32 entry,u32 owner,std::initializer_list<u32> args,u32& result)override{
  campaign_nickname_failed=entry;result=0;const auto a=args.begin();
  if(entry==0x482e40){if(args.size()!=7||a[0]!=0x72000000||!title_text_runtime)return false;auto vm=world->state(a[1]);std::string text;if(!vm.data||!name(a[6],text))return false;const std::vector<u8> bytes(text.begin(),text.end());if(!anm_text_literal(vm,boot_raster,a[2],a[3],signed_word(a[4]),signed_word(a[5]),bytes.data(),bytes.size(),*title_text_runtime))return false;campaign_nickname_text.push_back(text);return true;}
  if(entry==0x4845f0){if(args.size()!=0||owner<GameTitleRuntime::self||owner+4>GameTitleRuntime::self+GameTitleRuntime::bytes)return false;auto t=title_owner->view();const u32 at=owner-GameTitleRuntime::self;auto vm=world->find(t.get(at));if(!vm.data){t.put(at,0);return true;}result=vm.get(0x570);return true;}
  if(entry==0x45ea30){if(owner!=GameTitleRuntime::self||args.size()!=1||a[0]>=128)return false;auto t=title_owner->view();const u32 at=0x2c8+a[0]*4;if(!signal_animation(*world,t.get(at),1))return false;t.put(at,0);return true;}
  if(entry==0x402af0){if(args.size()!=0)return false;auto app=AnmView{common_renderer->application.data()};if(!capture_nickname_keyboard(campaign_nickname_current,true,app.get(0x724),title_device_host,result))return false;++campaign_nickname_captures;return true;}
  if(entry==0x446e20){if(args.size()!=0)return false;u32 token;if(!day1_notice_results_services.results_create_notice(owner,token))return false;title_activation_globals.trophy_owner=token;++campaign_nickname_created;return true;}
  if(entry==0x446d00){if(args.size()!=0||owner!=day1_notice_globals.owner)return false;auto state=day1_notice_view();if(!state.data||!destroy_notice(state,day1_notice_globals,day1_notice_services))return false;const u32 zero=0;if(!world->write(0x72bc7b58,&zero,4)||!world->write(0x72bc7b80,&zero,4))return false;title_root_load_words[0x4e6b80]=0;title_activation_globals.trophy_owner=0;++campaign_nickname_destroyed;return true;}
  if(entry==0x48a6e8)return args.size()==1&&day1_notice_storage.count(a[0])&&day1_notice_services.notice_release(a[0]);
  return CampaignOptionServices::title_option_call(entry,owner,args,result);
 }
 bool nickname_draw_read(u32 p,void* out,u32 n)override{return title_option_read(p,out,n);}
 bool nickname_draw_write(u32 p,const void* in,u32 n)override{return title_option_write(p,in,n);}
 bool nickname_ascii(u32 owner,std::array<u32,3>& position,u32 format,u32 value)override{if(owner!=GameAsciiRuntime::self||(format!=0x4c7d24&&format!=0x4c7d28))return false;std::string pattern;if(!name(format,pattern))return false;char text[64];const i32 n=std::snprintf(text,sizeof text,pattern.c_str(),signed_word(value));if(n<0||u32(n)>=sizeof text||!queue_ascii_text(game_ascii->view(),{real(position[0]),real(position[1]),real(position[2])},std::string_view(text,n),world->viewport))return false;++campaign_nickname_cells;return true;}
}campaign_nickname_services;
static bool campaign_nickname_title(u32& result){TitleNicknameEntryBindings b{title_owner->view(),{common_trophies->data.data()},common_save->view(),{campaign_nickname_scratch.data()},GameTitleRuntime::self};const bool ok=b.title.get(0x24)==1?advance_title_nickname_control(b,campaign_nickname_services,result):advance_title_nickname_entry(b,campaign_nickname_services,result);if(!ok)return false;++campaign_nickname_frames;campaign_nickname_failed=0;return world->synchronize_resources();}
static bool campaign_nickname_draw(u32& result){if(!draw_title_nickname(title_owner->view(),campaign_nickname_services,result))return false;++campaign_nickname_draws;return true;}
static bool campaign_nickname_notice(u32 owner,u32& result){if(owner!=day1_notice_globals.owner)return false;result=1;const bool ok=update_notice(day1_notice_view(),title_device.view().get(12),day1_notice_services);if(ok)day1_notice_failure=0;return ok;}
API(campaign_nickname_diagnostic)u32 campaign_nickname_diagnostic(u32 i){auto t=title_owner->view(),s=common_save->view(),r=AnmView{campaign_nickname_raw.data()};auto n=day1_notice_view();const u32 values[]={campaign_nickname_failed,campaign_nickname_frames,campaign_nickname_draws,u32(campaign_nickname_text.size()),campaign_nickname_captures,campaign_nickname_created,campaign_nickname_destroyed,t.get(0x24),t.get(0x28),t.get(0x30),r.get(0x100),r.get(0x104),s.get(0xf084),u32(s.data[0xefac])|(u32(s.data[0xefad])<<8),s.get(0xf16c),day1_notice_globals.owner,n.data?n.get(0x118):0,s.get(0xef2c),campaign_nickname_cells};return i<19?values[i]:0;}
API(campaign_nickname_text_count)u32 campaign_nickname_text_count(){return campaign_nickname_text.size();}
API(campaign_nickname_text_data)const char* campaign_nickname_text_data(u32 i){return i<campaign_nickname_text.size()?campaign_nickname_text[i].c_str():nullptr;}
API(campaign_nickname_unlocked)const u8* campaign_nickname_unlocked(){return common_save->data.data()+0xeff9;}

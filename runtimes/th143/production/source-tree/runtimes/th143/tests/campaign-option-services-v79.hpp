// Option composition. The audio globals are the actual manager tail fields
// (53b1e0+57a4..57ac), so existing music/SFX pumps consume the native settings.
static u32 campaign_option_failed=0,campaign_option_frames=0,campaign_option_views=0,campaign_option_sprites=0;
struct CampaignOptionServices:TitleOptionViewHost {
 u32 global_rate_token()const override{return world->global_rate_token();}
 bool timer_rate(u32 p,float& v)override{return world->timer_rate(p,v);}
 bool title_option_read(u32 p,void* out,u32 n)override{if(p>=0x53b1e0&&std::uint64_t(p)+n<=0x53b1e0+common_load_audio.size()){std::memcpy(out,common_load_audio.data()+p-0x53b1e0,n);return true;}return campaign_music_services.title_music_read(p,out,n);}
 bool title_option_write(u32 p,const void* in,u32 n)override{
  if(p>=0x53b1e0&&std::uint64_t(p)+n<=0x53b1e0+common_load_audio.size()){std::memcpy(common_load_audio.data()+p-0x53b1e0,in,n);return true;}
  if(p>=0x4e47d0&&std::uint64_t(p)+n<=0x4e47d0+common_renderer->application.size()){std::memcpy(common_renderer->application.data()+p-0x4e47d0,in,n);return true;}return campaign_music_services.title_music_write(p,in,n);
 }
 bool title_option_child(u32 self,u32 parent,i32 script,u32& token)override{if(self!=GameTitleRuntime::self||parent>=128)return false;auto vm=world->find(title_owner->view().get(0x2c8+parent*4));if(!vm.data){title_owner->view().put(0x2c8+parent*4,0);token=0;return true;}auto child=find_animation_child(static_cast<AnmWorld&>(*world),vm,script);token=child.data?child.get(0x570):0;return true;}
 bool title_option_call(u32 entry,u32 owner,std::initializer_list<u32> args,u32& result)override{
  campaign_option_failed=entry;result=0;const auto a=args.begin();
  if(entry==0x460540){if(owner!=GameTitleRuntime::self||!refresh_title_option_view(title_owner->view(),owner,*this))return false;++campaign_option_views;return true;}
  if(entry==0x473a00){if(args.size()!=2)return false;auto vm=world->state(a[0]);if(!vm.data||vm.get(0x30)!=owner||!anm_bind_sprite(vm,signed_word(a[1]),static_cast<AnmWorld&>(*world)))return false;++campaign_option_sprites;return true;}
  if(entry==0x484390)return args.size()==2&&signal_animation(static_cast<AnmWorld&>(*world),a[0],signed_word(a[1]),true,static_cast<AnmMenuWorld*>(world.get()));
  return campaign_music_services.title_music_call(entry,owner,args,result);
 }
}campaign_option_services;
static bool campaign_option_title(u32& result){if(!advance_title_option_control(title_owner->view(),GameTitleRuntime::self,campaign_option_services,result))return false;++campaign_option_frames;return world->synchronize_resources();}
API(campaign_option_diagnostic)u32 campaign_option_diagnostic(u32 i){auto a=AnmView{common_renderer->application.data()},s=AnmView{common_load_audio.data()};const u32 v[]={campaign_option_failed,campaign_option_frames,campaign_option_views,campaign_option_sprites,a.data[0x1f6],a.data[0x1f7],a.data[0x1f8],s.get(0x57a4),s.get(0x57a8),s.get(0x57ac),title_owner->view().get(0x1c),title_owner->view().get(0x24)};return i<12?v[i]:0;}

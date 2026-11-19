// Raw browser-device input is an explicit platform packet. No menu/save/game
//state is supplied by the browser; native-gated401e70 and461570 consume it.
static std::array<u8,128> campaign_pad_input_bytes{},campaign_pad_buttons{};
static u32 campaign_pad_connected=0,campaign_pad_x=32768,campaign_pad_y=32768,campaign_pad_pov=65535,campaign_pad_input_samples=0;
static u32 campaign_pad_failed=0,campaign_pad_frames=0,campaign_pad_views=0,campaign_pad_reads=0,campaign_pad_method=0;
struct CampaignPadServices:CampaignOptionServices,DevicePadButtonReadHost {
 bool pad_winmm_state(std::array<u8,52>& info,u32& status)override{
  campaign_pad_method=0;status=campaign_pad_connected?0:1;auto s=AnmView{info.data()};s.put(8,campaign_pad_x);s.put(12,campaign_pad_y);s.put(16,32768);s.put(20,32768);s.put(24,32768);s.put(28,32768);u32 mask=0;for(u32 i=0;i<32;++i)if(campaign_pad_input_bytes[i]&0x80)mask|=1u<<i;s.put(32,mask);s.put(36,0);s.put(40,campaign_pad_pov);return true;
 }
 bool pad_direct_poll(u32,u32& status)override{campaign_pad_method=1;status=campaign_pad_connected?0:0x8007000c;return true;}
 bool pad_direct_acquire(u32,u32& status)override{status=campaign_pad_connected?0:0x8007000c;return true;}
 bool pad_direct_state(u32,std::array<u8,272>& state,u32& status)override{state.fill(0);std::memcpy(state.data()+48,campaign_pad_input_bytes.data(),128);status=campaign_pad_connected?0:0x8007000c;return true;}
 bool title_option_read(u32 p,void* out,u32 n)override{
  if(p>=0x4e1c04&&std::uint64_t(p)+n<=0x4e1c18){std::memcpy(out,campaign_configuration.keyboard.data()+p-0x4e1c04,n);return true;}
  if(p>=0x540f30&&std::uint64_t(p)+n<=0x540fb0){std::memcpy(out,campaign_pad_buttons.data()+p-0x540f30,n);return true;}
  return CampaignOptionServices::title_option_read(p,out,n);
 }
 bool title_option_write(u32 p,const void* in,u32 n)override{if(p>=0x4e1c04&&std::uint64_t(p)+n<=0x4e1c18){std::memcpy(campaign_configuration.keyboard.data()+p-0x4e1c04,in,n);return true;}return CampaignOptionServices::title_option_write(p,in,n);}
 bool title_option_call(u32 entry,u32 owner,std::initializer_list<u32> args,u32& result)override{
  campaign_pad_failed=entry;
  if(entry==0x461870){result=0;if(owner!=GameTitleRuntime::self||!refresh_title_pad_config_view_v2(title_owner->view(),owner,*this))return false;++campaign_pad_views;return true;}
  if(entry==0x401e70){auto app=AnmView{common_renderer->application.data()};if(!read_device_pad_buttons(campaign_pad_buttons,app.get(0x724),app.get(0x24),*this))return false;++campaign_pad_reads;result=0x540f30;return true;}
  return CampaignOptionServices::title_option_call(entry,owner,args,result);
 }
}campaign_pad_services;
static bool campaign_pad_title(u32& result){if(!advance_title_pad_config(title_owner->view(),GameTitleRuntime::self,campaign_pad_services,result))return false;++campaign_pad_frames;return world->synchronize_resources();}
API(campaign_pad_input)u32 campaign_pad_input(const u8* bytes,u32 n,u32 connected,u32 x,u32 y,u32 pov){if(n!=128||x>65535||y>65535||pov>65535)return 0;std::memcpy(campaign_pad_input_bytes.data(),bytes,128);campaign_pad_connected=connected?1:0;campaign_pad_x=x;campaign_pad_y=y;campaign_pad_pov=pov;++campaign_pad_input_samples;return 1;}
API(campaign_pad_diagnostic)u32 campaign_pad_diagnostic(u32 i){if(i==0)return campaign_pad_failed;if(i==1)return campaign_pad_frames;if(i==2)return campaign_pad_views;if(i==3)return campaign_pad_reads;if(i==4)return campaign_pad_connected;if(i==5)return campaign_pad_input_samples;if(i<12){u16 v;std::memcpy(&v,title_owner->data.data()+0x5b38+(i-6)*2,2);return v;}if(i<22){u16 v;std::memcpy(&v,campaign_configuration.keyboard.data()+(i-12)*2,2);return v;}if(i==22){u32 mask=0;for(u32 j=0;j<32;++j)if(campaign_pad_buttons[j]&0x80)mask|=1u<<j;return mask;}if(i==23)return campaign_pad_method;if(i==24)return campaign_pad_x;if(i==25)return campaign_pad_y;return 0;}

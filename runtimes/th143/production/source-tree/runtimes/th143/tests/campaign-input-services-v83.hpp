// Browser axes and raw buttons are the same explicit software OS packet used
// by the config reader. Runtime controls come from the gated401fa0/401b70 path.
static u32 campaign_input_polls=0,campaign_input_failed=0;
struct CampaignInputServices:DeviceInputV2Host {
 bool keyboard_state(bool direct,std::array<u8,256>& out,u32& status)override{return title_device_host.keyboard_state(direct,out,status);}
 bool acquire_keyboard(u32& status)override{return title_device_host.acquire_keyboard(status);}
 bool joystick_memory_read(u32 p,void* out,u32 n)override{
  if(p>=0x4e1c04&&std::uint64_t(p)+n<=0x4e1c18){std::memcpy(out,title_device.data.data()+0x234+p-0x4e1c04,n);return true;}
  if(p>=0x540ae4&&std::uint64_t(p)+n<=0x540af4){const u32 range[]={0,65535,0,65535};std::memcpy(out,reinterpret_cast<const u8*>(range)+p-0x540ae4,n);return true;}
  return campaign_pad_services.title_option_read(p,out,n);
 }
 bool pad_winmm_state(std::array<u8,52>& out,u32& status)override{++campaign_input_polls;return campaign_pad_services.pad_winmm_state(out,status);}
 bool pad_direct_poll(u32 p,u32& status)override{return campaign_pad_services.pad_direct_poll(p,status);}
 bool pad_direct_acquire(u32 p,u32& status)override{return campaign_pad_services.pad_direct_acquire(p,status);}
 bool pad_direct_state(u32 p,std::array<u8,272>& out,u32& status)override{if(!campaign_pad_services.pad_direct_state(p,out,status))return false;const auto axis=[](u32 value){const float x=(float(value)/65535.f)*2000.f-1000.f;return u32(i32(x>=0?x+.5f:x-.5f));};AnmView view{out.data()};view.put(0,axis(campaign_pad_x));view.put(4,axis(campaign_pad_y));return true;}
}campaign_input_services;
static DeviceInputV2Host& campaign_input_platform(){
 //4e1c04 aliasesDevice234. The existing fixture keeps the canonical globals
 //beside the configuration platform; project those live bindings at dispatch.
 std::memcpy(title_device.data.data()+0x234,campaign_configuration.keyboard.data(),20);return campaign_input_services;
}
API(campaign_input_diagnostic)u32 campaign_input_diagnostic(u32 i){auto d=title_device.view();const u32 v[]={campaign_input_failed,campaign_input_polls,d.get(0),d.get(4),d.get(8),d.get(12),d.get(16),d.get(0x22c)};return i<8?v[i]:0;}

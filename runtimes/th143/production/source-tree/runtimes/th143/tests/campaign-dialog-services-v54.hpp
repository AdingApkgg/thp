// V54 cooperative composition. Component bodies are separately native-gated;
// scheduling and the concrete graphics/file platform remain integration scope.
static std::map<u32,std::vector<u8>> campaign_dialog_storage;
static u32 campaign_dialog_pending=0,campaign_dialog_resource=0,campaign_dialog_failed=0;
static std::array<u32,5> campaign_dialog_counts{};
static AnmView campaign_dialog_view(u32 p){auto i=campaign_dialog_storage.find(p);return {i==campaign_dialog_storage.end()?nullptr:i->second.data()};}
struct CampaignDialogServices:MessageDialogFactoryHost,MessageDialogLoadHost,MessageDialogUpdateHost,MessageDialogPageHost,MessageDialogCleanupHost,HudMessageDialogInstructionHost,SchedulerHost,TitlePreviewImageDevice {
 bool invoke(u32,u32,u32&)override{return false;}
 bool release_callback(u32 p)override{return common_load_storage.release_game_storage(p);}
 bool dialog_allocate(u32 n,u32& p,AnmView& out)override{
  if(!common_load_storage.allocate_game_storage(n,p)||!p)return false;
  if(n==0x28){if(!frames->scheduler.create(p,0,u8(fill)))return false;out=frames->scheduler.at(p);return true;}
  if(n!=0x1c4)return false;campaign_dialog_storage.emplace(p,std::vector<u8>(n,u8(fill)));out=campaign_dialog_view(p);return true;
 }
 bool dialog_update_callback(u32 entry,u32& p,AnmView& out)override{if(!common_load_storage.allocate_game_storage(0x28,p)||!frames->scheduler.create(p,entry,u8(fill)))return false;out=frames->scheduler.at(p);return true;}
 bool dialog_register(u32 p,i32 priority,bool draw)override{u32 result;return frames->scheduler.add(p,priority,draw,*this,result);}
 bool queue(u32 kind){if(campaign_dialog_pending)return false;campaign_dialog_pending=kind;auto app=AnmView{common_renderer->application.data()};app.put(0x99c,1);app.put(0x998,0);return true;}
 bool dialog_load_worker(u32 entry,u32 owner)override{return entry==0x468360&&owner==campaign_dialog_owner&&queue(1);}
 bool dialog_request_resource(u32 slot,u32 filename,u32& resource)override{resource=campaign_dialog_resource;return slot==19&&filename==0x4c5884&&resource;}
 bool dialog_resource_error(u32,u32)override{return false;}
 bool timer_rate(u32 p,float& r)override{return world->timer_rate(p,r);}
 bool dialog_update_read(u32 p,void* out,u32 n)override{
  for(auto& [base,bytes]:campaign_dialog_storage)if(p>=base&&std::uint64_t(p)+n<=std::uint64_t(base)+bytes.size()){std::memcpy(out,bytes.data()+p-base,n);return true;}
  auto copy=[&](u32 base,const void* data,u32 size){if(p<base||std::uint64_t(p)+n>std::uint64_t(base)+size)return false;std::memcpy(out,static_cast<const u8*>(data)+p-base,n);return true;};
  const u32 save=common_load_bindings->save_owner;
  if(copy(0x4e6b9c,&save,4)||copy(save,common_save->data.data(),common_save->data.size())||copy(0x4e6bc8,&campaign_dialog_owner,4))return true;
  if(p==0x4e19dc&&n==4){std::memcpy(out,&title_gameplay_fresh,4);return true;}
  return title_root_load_read(p,out,n)||world->read(p,out,n);
 }
 bool dialog_update_write(u32 p,const void* data,u32 n)override{
  for(auto& [base,bytes]:campaign_dialog_storage)if(p>=base&&std::uint64_t(p)+n<=std::uint64_t(base)+bytes.size()){std::memcpy(bytes.data()+p-base,data,n);return true;}
  if(p==0x4e47c4&&n==8){std::memcpy(&title_start_globals.statistics_time,data,8);return true;}
  if(p>=0x4e47d0&&std::uint64_t(p)+n<=0x4e47d0+common_renderer->application.size()){std::memcpy(common_renderer->application.data()+p-0x4e47d0,data,n);return true;}
  return world->write(p,data,n);
 }
 bool preload_preview_texture(u32 texture)override{return common_texture_resources->textures.images.count(texture)!=0;}
 bool clear_texture(u32 descriptor){
  u32 texture,surface;i32 status;if(!world->read(descriptor,&texture,4)||!common_texture_resources->textures.surface(texture,0,surface,status)||status<0)return false;
  auto i=common_texture_resources->textures.images.find(surface);if(i==common_texture_resources->textures.images.end())return false;auto& pixels=i->second.pixels;std::fill(pixels.data.begin(),pixels.data.end(),0);
  return common_texture_device.texture_uploaded(surface,pixels)&&common_texture_resources->textures.release(surface);
 }
 bool upload(u32 descriptor,u32 source,u32 size,u32 mode){
  if(mode!=1)return false;u32 texture,flags,bpp=2;if(!world->read(descriptor,&texture,4)||!world->read(descriptor+0x14,&flags,4))return false;flags&=~1u;
  if(!world->write(descriptor+0x14,&flags,4)||!world->write(descriptor+8,&size,4))return false;
  GameTitlePreviewImages images{*world,common_texture_resources->textures,common_texture_device,*this};
  if(!images.upload_png(texture,source,size)||!world->write(descriptor+0xc,&bpp,4))return false;++campaign_dialog_counts[2];return true;
 }
 bool dialog_update_call(u32 entry,u32 owner,std::initializer_list<u32> args,std::uint64_t& result)override{
  campaign_dialog_failed=entry;result=0;const auto a=args.begin();
  switch(entry){
   case 0x433830:{GameOverGlobals g;auto app=AnmView{common_renderer->application.data()};g.root_mode=title_root_state.view().get(0x94);g.application_state=app.get(0x6ec);g.clock=title_start_globals.clock;g.statistics_time=title_start_globals.statistics_time;if(!game_statistics_time(*common_save,g,title_gameplay_menu_host))return false;title_start_globals.clock=g.clock;title_start_globals.statistics_time=g.statistics_time;return true;}
   case 0x46f4e0:{double now;if(!title_start_globals.clock.sample(title_start_clock,now))return false;std::memcpy(&result,&now,8);return true;}
   case 0x484a40:return clear_texture(owner);
   case 0x472be0:return args.size()==1&&title_start_audio.request(a[0],false,0);
   case 0x481990:return args.size()==4&&upload(a[0],a[1],a[2],a[3]);
   case 0x48a7bc:return args.size()==1&&world->release_enemy_storage(a[0],true);
   case 0x24:return preload_preview_texture(owner);
   case 0x4682c0:return args.size()==3&&create_message_dialog_page(campaign_dialog_view(owner),{a[0],a[1],a[2]},*this);
   case 0x484390:return args.size()==2&&signal_animation(*world,a[0],signed_word(a[1]),true);
   case 0x431f80:result=(title_root_game.game_flags&0xc00)==0xc00;return true;
   case 0x436ee0:return title_root_cheat->end_scene();
   case 0x436c30:{if(args.size()!=1)return false;CheatSceneGlobals g{title_root_game.game_state[14],title_root_game.game_state[8],title_root_game.game_state[9],title_root_game.scene,title_root_menu->global_owner!=0,0,common_save->data[0xefac],common_save->data[0xf08a],{0,6,3,1,7,4,2,5,8}};return title_root_cheat->begin_scene(signed_word(a[0]),g);}
   case 0x41af40:{u32 resource,handle;if(!world->read(0x72bc7b0c+28*4,&resource,4)||!static_cast<AnmMenuWorld&>(*world).create_screen_transition(resource,handle))return false;result=handle;return true;}
   case 0x484320:return args.size()==2&&static_cast<AnmMenuWorld&>(*world).screen_transition_signal(a[0],signed_word(a[1]),false);
   case 0x41ce10:{if(args.size()!=2)return false;auto ascii=game_ascii->view();u32 handle=ascii.get(0x191ec);if(!root_transition(*world,ascii.get(0x191e4),handle,real(a[0]),real(a[1])))return false;ascii.put(0x191ec,handle);return true;}
   case 0x48aff2:{if(args.size()!=3||a[1]!=0x4c7fe8)return false;char filename[128];const auto count=std::snprintf(filename,sizeof filename,"tutorial%.2d.png",a[2]);return count>0&&u32(count)<sizeof filename&&dialog_update_write(a[0],filename,count+1);}
   case 0x444ad0:return owner==0x4e47d0&&args.size()==1&&a[0]==0x4683c0&&queue(2);
  }return false;
 }
 u32 dialog_page_current()const override{return campaign_dialog_owner;}
 AnmView dialog_page_owner(u32 p)override{return campaign_dialog_view(p);}
 bool dialog_page_file(u32 name,u32 size_out,u32& buffer)override{
  std::string filename;for(u32 i=0;i<128;++i){u8 value;if(!dialog_update_read(name+i,&value,1))return false;if(!value)break;filename+=char(value);if(i==127)return false;}
  std::vector<u8> bytes;if(!common_load_files.read_animation_file(filename,false,bytes))return false;const u32 size=bytes.size();
  return world->allocate_resource_storage(size,true,buffer)&&world->write(buffer,bytes.data(),size)&&dialog_update_write(size_out,&size,4);
 }
 bool dialog_page_visual(u32 resource,i32 script,const std::array<u32,3>& position,u32& handle)override{const std::array<float,3> p{real(position[0]),real(position[1]),real(position[2])};return common_pool_overlay.create(*world,resource,script,&p,0,-1,4,handle);}
 bool dialog_remove_callback(u32 p)override{return frames->scheduler.remove(p,*this);}
 bool dialog_destroy_resource(u32 p)override{return cleanup_anm_resource(p,{world->instances.registry.primary_head,world->instances.registry.secondary_head},*world);}
 bool dialog_free_storage(u32 p)override{auto i=campaign_dialog_storage.find(p);if(i!=campaign_dialog_storage.end()){campaign_dialog_storage.erase(i);return common_load_storage.release_game_storage(p);}return world->release_resource_storage(p);}
 bool message_dialog_create()override{u32 result;if(campaign_dialog_owner||!create_message_dialog(campaign_dialog_owner,result,*this))return false;++campaign_dialog_counts[0];return result!=0;}
 AnmView message_dialog_current()override{return campaign_dialog_view(campaign_dialog_owner);}
 bool message_dialog_read(u32 p,void* out,u32 n)override{return dialog_update_read(p,out,n);}
}campaign_dialog_services;
static bool campaign_dialog_create(){return campaign_dialog_services.message_dialog_create();}
static bool campaign_dialog_read(u32 p,void* out,u32 n){return campaign_dialog_services.dialog_update_read(p,out,n);}
static bool campaign_dialog_pump(){
 if(!campaign_dialog_pending)return true;if(!campaign_dialog_owner)return false;
 if(campaign_dialog_pending==1){
  if(!campaign_dialog_resource&&!world->request(19,"help.anm",campaign_dialog_resource))return false;
  i32 result;if(!world->pump(result))return false;u32 pending;if(!world->read(campaign_dialog_resource+0x128,&pending,4))return false;
  if(pending){++campaign_dialog_counts[4];return true;}
  auto s=campaign_dialog_view(campaign_dialog_owner);if(!load_message_dialog_resource(s,frames->scheduler.at(s.get(8)),frames->scheduler.at(s.get(12)),{common_renderer->application.data()},campaign_dialog_services))return false;
 }else if(campaign_dialog_pending==2){if(!load_message_dialog_page({common_renderer->application.data()},campaign_dialog_services))return false;++campaign_dialog_counts[1];}
 else return false;campaign_dialog_pending=0;return true;
}
static bool campaign_dialog_update(u32 owner,u32& result){auto s=campaign_dialog_view(owner);if(!s.data)return false;i32 value;if(!update_message_dialog(s,owner,campaign_dialog_services,value))return false;result=u32(value);return true;}
static bool campaign_dialog_destroy(u32 owner){
 auto s=campaign_dialog_view(owner);if(!s.data||owner!=campaign_dialog_owner)return false;u32 resource;if(!world->read(0x72bc7b58,&resource,4))return false;
 if(!destroy_message_dialog(owner,s,campaign_dialog_owner,resource,campaign_dialog_services)||!world->write(0x72bc7b58,&resource,4))return false;campaign_dialog_resource=0;++campaign_dialog_counts[3];return true;
}
API(campaign_dialog_diagnostic) u32 campaign_dialog_diagnostic(u32 i){if(i<5)return campaign_dialog_counts[i];if(i==5)return campaign_dialog_owner;if(i==6)return campaign_dialog_pending;if(i==7)return campaign_dialog_failed;auto s=campaign_dialog_view(campaign_dialog_owner);const u32 fields[]={0x10,0x18,0x28,0x128,0x130,0x134,0x138,0x13c,0x124};return s.data&&i-8<9?s.get(fields[i-8]):0;}

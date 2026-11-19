// Cooperative composition of the five separately native-gated Manual bodies.
// Raw resources, scheduler callbacks and PNG texture uploads use the game hosts.
static std::map<u32,std::vector<u8>> campaign_manual_storage;
static u32 campaign_manual_owner=0,campaign_manual_pending=0,campaign_manual_resource=0,campaign_manual_failed=0;
static std::array<u32,6> campaign_manual_counts{};
static std::vector<std::string> campaign_manual_pages;
static AnmView campaign_manual_view(u32 p){auto i=campaign_manual_storage.find(p);return {i==campaign_manual_storage.end()?nullptr:i->second.data()};}
struct CampaignManualServices:ManualDialogFactoryHost,ManualDialogWorkersHost,ManualDialogCleanupHost,ManualDialogUpdateHost,TitleManualPageHost,PauseManualPageHost,SchedulerHost,TitlePreviewImageDevice {
 bool invoke(u32,u32,u32&)override{return false;}
 bool release_callback(u32 p)override{return common_load_storage.release_game_storage(p);}
 u32 global_rate_token()const override{return world->global_rate_token();}
 bool timer_rate(u32 p,float& rate)override{return world->timer_rate(p,rate);}
 bool manual_allocate(u32 n,u32& p,AnmView& out)override{
  if(!common_load_storage.allocate_game_storage(n,p)||!p)return false;
  if(n==0x28){if(!frames->scheduler.create(p,0,u8(fill)))return false;out=frames->scheduler.at(p);return true;}
  if(n!=0x1c0)return false;campaign_manual_storage.emplace(p,std::vector<u8>(n,u8(fill)));out=campaign_manual_view(p);return true;
 }
 bool manual_update_callback(u32 entry,u32& p,AnmView& out)override{if(!common_load_storage.allocate_game_storage(0x28,p)||!frames->scheduler.create(p,entry,u8(fill)))return false;out=frames->scheduler.at(p);return true;}
 bool manual_register(u32 p,i32 priority,bool drawing)override{u32 result;return frames->scheduler.add(p,priority,drawing,*this,result);}
 bool queue(u32 kind){if(campaign_manual_pending||campaign_dialog_pending)return false;campaign_manual_pending=kind;auto app=AnmView{common_renderer->application.data()};app.put(0x99c,1);app.put(0x998,0);return true;}
 bool manual_load_worker(u32 entry,u32 owner)override{return entry==0x434510&&owner==campaign_manual_owner&&queue(1);}
 bool manual_region(u32 p,u32 n,AnmView& out)override{
  for(auto& [base,bytes]:campaign_manual_storage)if(p>=base&&std::uint64_t(p)+n<=std::uint64_t(base)+bytes.size()){out={bytes.data()+p-base};return true;}
  out=frames->scheduler.at(p);return out.data&&n<=0x28;
 }
 bool manual_request_resource(u32 slot,u32 name,u32& resource)override{resource=campaign_manual_resource;return slot==19&&name==0x4c5884&&resource;}
 bool manual_resource_error(u32,u32)override{return false;}
 bool read(u32 p,void* out,u32 n){
  auto copy=[&](u32 base,const void* data,u32 size){if(p<base||std::uint64_t(p)+n>std::uint64_t(base)+size)return false;std::memcpy(out,static_cast<const u8*>(data)+p-base,n);return true;};
  for(auto& [base,bytes]:campaign_manual_storage)if(copy(base,bytes.data(),bytes.size()))return true;
  const u32 ascii=GameAsciiRuntime::self;
  if(copy(0x4e6b60,&campaign_manual_owner,4)||copy(0x4e69f8,&ascii,4)||copy(ascii,game_ascii->data.data(),game_ascii->data.size())||copy(0x4e47d0,common_renderer->application.data(),common_renderer->application.size()))return true;
  if(p==0x4e19dc&&n==4){const u32 v=title_device.view().get(12);std::memcpy(out,&v,4);return true;}
  if(p==0x4e19d8&&n==4){const u32 v=title_device.view().get(8);std::memcpy(out,&v,4);return true;}
  return world->read(p,out,n);
 }
 bool write(u32 p,const void* data,u32 n){
  for(auto& [base,bytes]:campaign_manual_storage)if(p>=base&&std::uint64_t(p)+n<=std::uint64_t(base)+bytes.size()){std::memcpy(bytes.data()+p-base,data,n);return true;}
  for(auto& r:world->resources)if(p==r.token+0x134&&n==4){u32 count;std::memcpy(&count,data,4);world->instances.resource_uses[r.token]=count;break;}
  return world->write(p,data,n);
 }
 bool manual_update_read(u32 p,void* out,u32 n)override{return read(p,out,n);}
 bool title_manual_read(u32 p,void* out,u32 n)override{return read(p,out,n);}
 bool title_manual_write(u32 p,const void* data,u32 n)override{return write(p,data,n);}
 bool manual_read_page(u32 name,u32 size_out,u32 external,u32& buffer)override{
  if(external)return false;std::string filename;for(u32 i=0;i<128;++i){u8 value;if(!read(name+i,&value,1))return false;if(!value)break;filename+=char(value);if(i==127)return false;}
  std::vector<u8> bytes;if(!common_load_files.read_animation_file(filename,false,bytes))return false;const u32 n=bytes.size();
  if(!world->allocate_resource_storage(n,true,buffer)||!world->write(buffer,bytes.data(),n)||!write(size_out,&n,4))return false;campaign_manual_pages.push_back(filename);return true;
 }
 bool preload_preview_texture(u32 texture)override{return common_texture_resources->textures.images.count(texture)!=0;}
 bool upload(u32 descriptor,u32 source,u32 size,u32 mode){
  if(mode!=1)return false;u32 texture,flags,bpp=2;if(!world->read(descriptor,&texture,4)||!world->read(descriptor+0x14,&flags,4))return false;flags&=~1u;
  if(!world->write(descriptor+0x14,&flags,4)||!world->write(descriptor+8,&size,4))return false;
  GameTitlePreviewImages images{*world,common_texture_resources->textures,common_texture_device,*this};
  if(!images.upload_png(texture,source,size)||!world->write(descriptor+0xc,&bpp,4))return false;++campaign_manual_counts[2];return true;
 }
 bool manual_update_call(u32 entry,u32 owner,std::initializer_list<u32> args,u32& result)override{
  campaign_manual_failed=entry;result=0;const auto a=args.begin();
  switch(entry){
   case 0x432000:{if(args.size()!=4)return false;const std::array<float,3> p{real(a[1]),real(a[2]),real(a[3])};return common_pool_overlay.create(*world,owner,signed_word(a[0]),&p,0,-1,4,result);}
   case 0x484a40:return campaign_dialog_services.clear_texture(owner);
   case 0x472be0:return args.size()==1&&(AnmView{common_renderer->application.data()}.get(0x6e8)==7?title_start_audio.request(a[0],false,0):title_ready_sound_host.title_sound(a[0]));
   case 0x481990:return args.size()==4&&upload(a[0],a[1],a[2],a[3]);
   case 0x48a7bc:return args.size()==1&&world->release_enemy_storage(a[0],true);
   case 0x24:return preload_preview_texture(owner);
   case 0x484390:return args.size()==2&&signal_animation(*world,a[0],signed_word(a[1]),true);
   case 0x484320:return args.size()==2&&signal_animation(*world,a[0],signed_word(a[1]),false);
   case 0x48aff2:{if(args.size()!=3||a[1]!=0x4c58c4)return false;char name[128];const auto n=std::snprintf(name,sizeof name,"help_%.2d.png",a[2]);return n>0&&u32(n)<sizeof name&&write(a[0],name,n+1);}
   case 0x444ad0:return owner==0x4e47d0&&args.size()==1&&a[0]==0x434570&&queue(2);
  }return false;
 }
 bool manual_remove_callback(u32 p)override{return frames->scheduler.remove(p,*this);}
 bool manual_destroy_resource(u32 p)override{return cleanup_anm_resource(p,{world->instances.registry.primary_head,world->instances.registry.secondary_head},*world);}
 bool manual_free_storage(u32 p)override{auto i=campaign_manual_storage.find(p);if(i!=campaign_manual_storage.end()){campaign_manual_storage.erase(i);return common_load_storage.release_game_storage(p);}return world->release_resource_storage(p);}
 bool cleanup(u32 owner){auto s=campaign_manual_view(owner);if(!s.data||owner!=campaign_manual_owner)return false;u32 resource;if(!world->read(0x72bc7b58,&resource,4)||!cleanup_manual_dialog(s,campaign_manual_owner,resource,*this)||!world->write(0x72bc7b58,&resource,4))return false;campaign_manual_resource=0;++campaign_manual_counts[3];return true;}
 bool pause_manual_read(u32 p,void* out,u32 n)override{return read(p,out,n);}
 bool pause_manual_write(u32 p,const void* in,u32 n)override{return write(p,in,n);}
 bool pause_manual_call(u32 entry,u32 owner,std::initializer_list<u32> args)override{
  campaign_manual_failed=entry;auto& menu=title_root_menu->menu;auto m=menu.view();
  switch(entry){
   case 0x484730:case 0x4846f0:return owner==GameMenuRuntime::self+0x1e8&&world->flag(m.get(0x1e8),entry==0x4846f0);
   case 0x4347b0:{u32 result;return title_manual_call(entry,0,{},result);}
   case 0x434860:{const u32 p=campaign_manual_owner;return !p||(cleanup(p)&&manual_free_storage(p));}
   case 0x447630:if(owner!=GameMenuRuntime::self||args.size()!=1)return false;menu.substate(signed_word(*args.begin()));return true;
   case 0x4087f0:{if(owner!=GameMenuRuntime::self+0x10||args.size()!=1||*args.begin()!=0)return false;auto t=m.sub(0x10);if(!(t.get(16)&1)){t.put(12,global_rate_token());t.put(16,t.get(16)|1);}t.put(0,0xffffffff);t.put(4,0);t.put(8,0);return true;}
  }return false;
 }
 bool title_manual_call(u32 entry,u32 owner,std::initializer_list<u32> args,u32& result)override{
  campaign_manual_failed=entry;result=0;const auto a=args.begin();
  switch(entry){
   case 0x484de0:{AnmView vm;return world->acquire_state(result,vm);}
   case 0x40ab20:{if(args.size()!=2)return false;auto* r=world->resource(owner);auto vm=world->state(a[0]);if(!r||a[1]>=r->templates.size()||!vm.data)return false;anm_copy_template(vm,a[0],{r->templates[a[1]].data()},world->global_rate_token());return true;}
   case 0x474710:{auto vm=world->state(owner);return vm.data&&anm_step(vm,static_cast<AnmWorld&>(*world))!=-2;}
   case 0x483a70:{if(args.size()!=1)return false;auto vm=world->state(a[0]);return vm.data&&world->instances.registry.insert(vm,a[0],false,false,result)&&world->synchronize_resources();}
   case 0x45e970:{if(owner!=GameTitleRuntime::self||args.size()!=1)return false;u32 handle;if(!world->create_at(title_owner->view().get(0x14),signed_word(a[0]),-1,{0,0,0},handle))return false;title_owner->view().put(0x2c8+a[0]*4,handle);return true;}
   case 0x4347b0:if(campaign_manual_owner||campaign_dialog_owner||!create_manual_dialog(campaign_manual_owner,result,*this))return false;++campaign_manual_counts[0];return result!=0;
   case 0x484320:return args.size()==2&&signal_animation(*world,a[0],signed_word(a[1]),false);
   case 0x45e880:return owner==GameTitleRuntime::self&&args.size()==1&&select_title_state(*title_owner,signed_word(a[0]));
   case 0x4346c0:return cleanup(owner);
   case 0x48a6e8:return args.size()==1&&manual_free_storage(a[0]);
  }return false;
 }
}campaign_manual_services;
static bool campaign_manual_pump(){
 if(!campaign_manual_pending)return true;if(!campaign_manual_owner)return false;
 if(campaign_manual_pending==1){
  if(!campaign_manual_resource&&!world->request(19,"help.anm",campaign_manual_resource))return false;
  i32 result;if(!world->pump(result))return false;u32 pending;if(!world->read(campaign_manual_resource+0x128,&pending,4))return false;
  if(pending){++campaign_manual_counts[4];return true;}
  if(!load_manual_dialog_resource(campaign_manual_owner,{common_renderer->application.data()},campaign_manual_services))return false;
 }else if(campaign_manual_pending==2){if(!read_manual_dialog_page(campaign_manual_owner,{common_renderer->application.data()},campaign_manual_services))return false;++campaign_manual_counts[1];}
 else return false;campaign_manual_pending=0;return true;
}
static bool campaign_manual_update(u32 owner,u32& result){auto s=campaign_manual_view(owner);if(!s.data)return false;i32 value;if(!update_manual_dialog(s,owner,campaign_manual_services,value))return false;result=u32(value);++campaign_manual_counts[5];return true;}
static bool campaign_manual_title(u32& result){return advance_title_manual_page(title_owner->view(),GameTitleRuntime::self,campaign_manual_services,result)&&world->synchronize_resources();}
API(campaign_manual_diagnostic) u32 campaign_manual_diagnostic(u32 i){if(i<6)return campaign_manual_counts[i];if(i==6)return campaign_manual_owner;if(i==7)return campaign_manual_pending;if(i==8)return campaign_manual_failed;auto s=campaign_manual_view(campaign_manual_owner);const u32 fields[]={0x10,0x18,0x28,0x128,0x130,0x134,0x138,0x124,0x12c};return s.data&&i-9<9?s.get(fields[i-9]):0;}
API(campaign_manual_page_count) u32 campaign_manual_page_count(){return campaign_manual_pages.size();}
API(campaign_manual_page_name) const char* campaign_manual_page_name(u32 i){return i<campaign_manual_pages.size()?campaign_manual_pages[i].c_str():nullptr;}

static bool campaign_manual_pause(AnmView menu,u32 self,u32 state){return state==12&&advance_pause_manual_page(menu,self,campaign_manual_services);}

// Music Room composition over the same title scheduler, ANM world and audio
// queue. Individual control, entry, parser and interpolation bodies are gated.
static u32 campaign_music_failed=0,campaign_music_frames=0,campaign_music_files=0,campaign_music_texts=0,campaign_music_queues=0,campaign_music_last_kind=0;
static std::vector<std::string> campaign_music_loads;
struct CampaignMusicServices:TitleMusicEntryHost {
 u32 global_rate_token()const override{return world->global_rate_token();}
 bool timer_rate(u32 p,float& value)override{return world->timer_rate(p,value);}
 bool title_music_read(u32 p,void* out,u32 n)override{
  auto copy=[&](u32 base,const void* data,u32 size){if(p<base||std::uint64_t(p)+n>std::uint64_t(base)+size)return false;std::memcpy(out,static_cast<const u8*>(data)+p-base,n);return true;};
  const u32 save=common_load_bindings->save_owner,pool=0x72000000;
  if(copy(0x4e6b9c,&save,4)||copy(save,common_save->data.data(),common_save->data.size())||copy(0x538de8,&pool,4)||copy(GameTitleRuntime::self,title_owner->data.data(),title_owner->data.size()))return true;
  return campaign_manual_services.read(p,out,n);
 }
 bool title_music_write(u32 p,const void* data,u32 n)override{
  const u32 save=common_load_bindings->save_owner;if(p>=save&&std::uint64_t(p)+n<=std::uint64_t(save)+common_save->data.size()){std::memcpy(common_save->data.data()+p-save,data,n);return true;}
  return campaign_manual_services.write(p,data,n);
 }
 bool name(u32 p,std::string& out){out.clear();for(u32 i=0;i<512;++i){u8 c;if(!title_music_read(p+i,&c,1))return false;if(!c)return true;out.push_back(char(c));}return false;}
 bool title_music_file(u32 filename,u32& token,u32& declared,std::vector<u8>& backing)override{
  campaign_music_failed=0x402e00;std::string path;if(!name(filename,path)||path!="musiccmt.txt")return false;
  if(!common_load_files.read_animation_file(path,false,backing)){token=declared=0;return true;}declared=backing.size();backing.insert(backing.end(),64,0);
  if(!world->allocate_resource_storage(backing.size(),true,token)||!world->write(token,backing.data(),backing.size()))return false;++campaign_music_files;return true;
 }
 bool queue(u32 kind,u32 parameter,const std::string& path){MusicCommandQueue q;std::memcpy(q.data.data(),common_load_audio.data()+0x24f8,q.data.size());if(!q.enqueue(kind,parameter,path.c_str()))return false;std::memcpy(common_load_audio.data()+0x24f8,q.data.data(),q.data.size());++campaign_music_queues;campaign_music_last_kind=kind;return true;}
 bool title_music_call(u32 entry,u32 owner,std::initializer_list<u32> args,u32& result)override{
  campaign_music_failed=entry;result=0;const auto a=args.begin();
  switch(entry){
   case 0x484de0:case 0x40ab20:case 0x474710:case 0x483a70:case 0x45e970:case 0x45e880:return campaign_manual_services.title_manual_call(entry,owner,args,result);
   case 0x484280:case 0x4845f0:{u32 handle;if(entry==0x484280){if(args.size()!=1)return false;handle=a[0];}else if(!title_music_read(owner,&handle,4))return false;auto vm=world->find(handle);result=vm.data?vm.get(0x570):0;return true;}
   case 0x482c20:{
    if(args.size()!=8&&args.size()!=9)return false;auto vm=world->state(a[1]);std::string text;if(!vm.data||!title_text_runtime||!name(a[7],text))return false;
    if(args.size()==9){if(a[7]!=0x4c7e54)return false;char formatted[120];const i32 n=std::snprintf(formatted,sizeof formatted,text.c_str(),signed_word(a[8]));if(n<0||u32(n)>=sizeof formatted)return false;text.assign(formatted,n);}
    const std::vector<u8> bytes(text.begin(),text.end());if(!title_text_runtime->draw_literal(vm,bytes,a[2],a[3],signed_word(a[4]),signed_word(a[5]),signed_word(a[6])))return false;++campaign_music_texts;return true;
   }
   case 0x410ea0:{if(args.size()!=1)return false;auto vm=world->state(owner);return vm.data&&signal_animation_vm(static_cast<AnmWorld&>(*world),vm,signed_word(a[0]),false,static_cast<AnmMenuWorld*>(world.get()));}
   case 0x418300:{
    if(args.size()!=6||a[2]!=owner+0x3c)return false;auto vm=world->state(owner);std::array<u32,3> from,zero,to{a[3],a[4],a[5]};if(!vm.data||!title_music_read(a[2],from.data(),12)||!title_music_read(0x53b184,zero.data(),12))return false;begin_anm_position_interpolation(vm,a[0],a[1],from,to,zero);return true;
   }
   case 0x45e900:{if(owner!=GameTitleRuntime::self||args.size()!=1)return false;auto t=title_owner->view();t.put(0x24,a[0]);if(!(t.get(0x2c4)&1)){t.put(0x2c0,global_rate_token());t.put(0x2c4,t.get(0x2c4)|1);}t.put(0x2b4,0xffffffff);t.put(0x2b8,0);t.put(0x2bc,0);return true;}
   case 0x472be0:return args.size()==1&&title_ready_sound_host.title_sound(a[0]);
   case 0x484320:return args.size()==2&&signal_animation(static_cast<AnmWorld&>(*world),a[0],signed_word(a[1]),false,static_cast<AnmMenuWorld*>(world.get()));
   case 0x4737b0:{if(owner!=0x53b1e0||args.size()!=3)return false;std::string path;return name(a[2],path)&&queue(a[0],a[1],path);}
   case 0x444660:{if(args.size()!=1)return false;std::string path;if(!name(a[0],path))return false;MusicCommandQueue q;MusicScene scene;std::memcpy(q.data.data(),common_load_audio.data()+0x24f8,q.data.size());if(!scene.load(q,path.c_str()))return false;std::memcpy(common_load_audio.data()+0x24f8,q.data.data(),q.data.size());campaign_music_loads.push_back(path);++campaign_music_queues;campaign_music_last_kind=1;result=1;return true;}
   case 0x4446e0:{if(args.size()!=2)return false;MusicCommandQueue q;std::memcpy(q.data.data(),common_load_audio.data()+0x24f8,q.data.size());if(!q.start(*common_save,a[0],a[1],AnmView{common_renderer->application.data()}.get(0x20c)))return false;std::memcpy(common_load_audio.data()+0x24f8,q.data.data(),q.data.size());++campaign_music_queues;campaign_music_last_kind=2;return true;}
   case 0x48a7bc:return args.size()==1&&world->release_enemy_storage(a[0],true);
  }
  if(args.size()==1){auto vm=world->state(owner);if(vm.data&&vm.get(0x5c4)==entry)return signal_animation_vm(static_cast<AnmWorld&>(*world),vm,signed_word(a[0]),false,static_cast<AnmMenuWorld*>(world.get()));}
  return false;
 }
}campaign_music_services;
static bool campaign_music_title(u32& result){auto t=title_owner->view();const bool ok=t.get(0x24)==0?advance_title_music_entry(t,GameTitleRuntime::self,campaign_music_services,result):advance_title_music_control(t,GameTitleRuntime::self,campaign_music_services,result);if(!ok)return false;++campaign_music_frames;return world->synchronize_resources();}
API(campaign_music_diagnostic)u32 campaign_music_diagnostic(u32 i){auto t=title_owner->view();const u32 values[]={campaign_music_failed,campaign_music_frames,campaign_music_files,campaign_music_texts,u32(campaign_music_loads.size()),campaign_music_queues,campaign_music_last_kind,t.get(0x7f4),t.get(0x7f8),t.get(0x7fc),t.get(0x800),t.get(0x5a44),common_save->data[0xef74]};return i<13?values[i]:0;}
API(campaign_music_load_count)u32 campaign_music_load_count(){return campaign_music_loads.size();}
API(campaign_music_load_name)const char* campaign_music_load_name(u32 i){return i<campaign_music_loads.size()?campaign_music_loads[i].c_str():nullptr;}

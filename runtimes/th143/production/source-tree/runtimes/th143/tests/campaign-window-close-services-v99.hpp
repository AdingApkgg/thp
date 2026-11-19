// Software composition of the separately gated46e770 and443a00 bodies.
// Win32 COM/font/archive releases are logical browser platform boundaries.
static u32 campaign_window_requested=0,campaign_window_closed=0,campaign_window_failed=0,campaign_window_audio_mode=0,campaign_window_bitmap_deleted=0;
static std::vector<u32> campaign_window_events;
struct CampaignWindowCleanup:CampaignQuitCleanup {
 bool cleanup_destructor(u32 entry,u32 owner)override{
  if(entry==0x45f370&&owner==GameTitleRuntime::self){campaign_quit_failed=entry;campaign_quit_events.insert(campaign_quit_events.end(),{entry,owner});campaign_quit_storage.deferred=owner;auto& b=*title_bindings;TitleLoadBindings local{b.title,b.common,b.frames,b.cheat,b.resources,campaign_quit_storage,b.save,b.application,b.globals,b.equipment,b.saved_equipment,b.alternate,b.global_538de4};local.loaded_save=b.loaded_save;return destroy_title(local,campaign_quit_worker,campaign_replay_cleanup_host());}
  if(entry==0x432a30&&owner==title_root_globals.root){campaign_quit_storage.deferred=owner;return title_retry_cleanup.cleanup(false);}
  if(entry==0x4346c0&&owner==campaign_manual_owner){campaign_quit_storage.deferred=owner;return campaign_manual_services.cleanup(owner);}
  if(entry==0x468510&&owner==campaign_dialog_owner){campaign_quit_storage.deferred=owner;u32 resource;if(!world->read(0x72bc7b58,&resource,4)||!cleanup_message_dialog(campaign_dialog_view(owner),campaign_dialog_owner,resource,campaign_dialog_services)||!world->write(0x72bc7b58,&resource,4))return false;campaign_dialog_resource=0;++campaign_dialog_counts[3];return true;}
  return CampaignQuitCleanup::cleanup_destructor(entry,owner);
 }
 bool cleanup_free(u32 owner)override{if(campaign_manual_storage.count(owner)){campaign_quit_storage.deferred=0;return campaign_manual_services.manual_free_storage(owner);}if(campaign_dialog_storage.count(owner)){campaign_quit_storage.deferred=0;return campaign_dialog_services.dialog_free_storage(owner);}return CampaignQuitCleanup::cleanup_free(owner);}
}campaign_window_cleanup;
struct CampaignWindowWorker:CampaignQuitWorker {
 bool wait_worker(u32 h,u32 ms,u32& r)override{return h>=0x77770101&&h<=0x77770200?title_retry_platform.wait_worker(h,ms,r):CampaignQuitWorker::wait_worker(h,ms,r);}
 bool close_worker(u32 h)override{return h>=0x77770101&&h<=0x77770200?title_retry_platform.close_worker(h):CampaignQuitWorker::close_worker(h);}
}campaign_window_worker;
struct CampaignWindowShutdown:ApplicationShutdownHost {
 bool shutdown_read(u32 p,u32& v)override{
  if(p==0x4e6b9c){v=common_load_bindings->save_owner;return true;}if(p==0x4e6a50){auto* t=campaign_live_timing();v=t?t->global_owner:0;return true;}if(p==0x538de8){v=0x72000000;return true;}
  constexpr u32 fonts[]={0x540df8,0x540dfc,0x540e00,0x540e08,0x540e04,0x540e0c,0x540e10,0x540e18,0x540e14,0x540e1c};for(u32 i=0;i<10;++i)if(p==fonts[i]){v=application_boot->fonts.handles[i];return true;}
  if(title_root_load_read(p,&v,4)||common_application_targets->read_render_memory(p,&v,4))return true;campaign_window_failed=p;return false;
 }
 bool shutdown_write(u32 p,u32 v)override{
  if(p==0x540978){campaign_window_audio_mode=v;std::memcpy(common_load_audio.data()+0x5798,&v,4);return true;}
  if(p>=0x4e47d0&&p+4<=0x4e5204){AnmView{common_renderer->application.data()}.put(p-0x4e47d0,v);return true;}if(common_application_targets->write_render_memory(p,&v,4))return true;campaign_window_failed=p;return false;
 }
 bool shutdown_call(u32 entry,u32 owner,std::initializer_list<u32> args,u32& result)override{
  campaign_window_failed=entry;campaign_window_events.insert(campaign_window_events.end(),{entry,owner,u32(args.size())});campaign_window_events.insert(campaign_window_events.end(),args);result=0;const auto a=args.begin();
  switch(entry){
   case 0x4562e0:return write_save_file(*common_save,common_saved_equipment,*world,title_gameplay_save,common_loaded_save.get());
   case 0x472df0:return campaign_pump_audio(result);
   case 0x403e90:{BackgroundWorker worker;auto app=AnmView{common_renderer->application.data()};std::memcpy(worker.data.data(),app.data+0x98c,worker.data.size());const bool ok=stop_background_worker(worker,campaign_window_worker);std::memcpy(app.data+0x98c,worker.data.data(),worker.data.size());return ok;}
   case 0x443c30:return cleanup_application_owners(campaign_window_cleanup);
   case 0x42bd30:{auto* t=campaign_live_timing();return t&&t->global_owner==owner&&t->destroy();}
   case 0x4737b0:{if(owner!=0x53b1e0||args.size()!=3||a[0]!=4||a[1]||a[2]!=0x4c61a4)return false;MusicCommandQueue q;std::memcpy(q.data.data(),common_load_audio.data()+0x24f8,q.data.size());if(!q.enqueue(4,0,"dummy"))return false;std::memcpy(common_load_audio.data()+0x24f8,q.data.data(),q.data.size());return true;}
   case 0x46ad40:boot_raster.bitmap.clear();campaign_window_bitmap_deleted=1;return true;
   case 0x4b8038:return args.size()==1; // Virtual font handles have no persistent OS objects.
   case 0x20:return args.size()==1; // Virtual DirectInput Unacquire, after input delivery stops.
   case 8:if(args.size()!=1||a[0]!=owner)return false;if(owner==0x6e037000)return true;if(common_texture_resources->textures.images.count(owner))return common_texture_resources->textures.release(owner);return true; // Logical caller-provided COM interfaces.
   case 0x468ba0:return owner==0x538f50; // Raw hash-pinned archive inputs are browser-owned.
   case 0x48a7bc:return args.size()==1&&world->release_resource_storage(a[0]);
   case 0x48a6e8:return args.size()==1&&common_load_storage.release_game_storage(a[0]);
  }return false;
 }
}campaign_window_shutdown;
struct CampaignWindowMessage:WindowMessageDispatchHost {
 bool window_message_read(u32 p,u32& v)override{return campaign_window_shutdown.shutdown_read(p,v);}
 bool window_message_write(u32 p,u32 v)override{return campaign_window_shutdown.shutdown_write(p,v);}
 bool window_message_call(u32,std::initializer_list<u32>,u32&)override{return false;}
}campaign_window_message;
API(campaign_window_close_request)u32 campaign_window_close_request(){u32 result;if(!dispatch_window_message(0,0x10,0,0,campaign_window_message,result))return 0;++campaign_window_requested;return result;}
static bool campaign_finish_shutdown_tail(){
 if(campaign_window_closed)return true;if(!shutdown_application(0x4e47d0,campaign_window_shutdown))return false;auto app=AnmView{common_renderer->application.data()};constexpr u8 prefix[]={0};if(!write_exit_configuration(app,prefix,sizeof prefix,campaign_quit_write)){campaign_window_failed=0x403040;return false;}campaign_window_failed=campaign_quit_failed=0;campaign_window_closed=campaign_quit_closed=1;campaign_cold_title_active=false;return true;
}
API(campaign_window_close_finish)u32 campaign_window_close_finish(){return campaign_window_requested&&campaign_finish_shutdown_tail();}
API(campaign_window_close_diagnostic)u32 campaign_window_close_diagnostic(u32 i){const u32 v[]={campaign_window_failed,campaign_window_requested,campaign_window_closed,campaign_window_audio_mode,campaign_window_bitmap_deleted,u32(campaign_window_events.size()),title_root_globals.root,campaign_manual_owner,campaign_dialog_owner,u32(world->releases.size())};return i<10?v[i]:0;}
API(campaign_window_close_events_data)const u32* campaign_window_close_events_data(){return campaign_window_events.data();}
API(campaign_window_close_events_words)u32 campaign_window_close_events_words(){return campaign_window_events.size();}

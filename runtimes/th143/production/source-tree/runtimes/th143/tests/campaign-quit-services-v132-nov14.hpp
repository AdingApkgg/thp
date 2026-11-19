// Main-menu Quit composition. Destructors execute after the scheduler returns;
// no callbacks run against the released Common/Title storage afterward.
struct CampaignQuitWorker:RootFactoryHost {
 bool allocate_root(u32&)override{return false;}bool evict_managed_textures()override{return false;}bool sleep_worker(u32)override{return false;}bool launch_worker(u32,u32,u32,u32&,u32&)override{return false;}
 bool wait_worker(u32 handle,u32 ms,u32& result)override{if(handle==0x77770005){if(ms!=200||campaign_replay_pending)return false;result=0;return true;}if(handle==0x77770003)return title_scene_worker.wait_worker(handle,ms,result);if(handle==0x77770004)return title_scene_handoff_worker.wait_worker(handle,ms,result);return false;}
 bool close_worker(u32 handle)override{if(handle==0x77770005)return !campaign_replay_pending;if(handle==0x77770003)return title_scene_worker.close_worker(handle);if(handle==0x77770004)return title_scene_handoff_worker.close_worker(handle);return false;}
}campaign_quit_worker;
static u32 campaign_quit_failed=0,campaign_quit_frames=0,campaign_quit_closed=0,campaign_quit_signal=0;
static std::vector<u32> campaign_quit_events;
struct CampaignQuitControl:TitleQuitControlHost {
 bool timer_rate(u32 p,float& f)override{return world->timer_rate(p,f);}
 bool title_quit_read(u32 p,u32& v)override{if(p<0x4e47d0||p+4>0x4e5204)return false;v=AnmView{common_renderer->application.data()}.get(p-0x4e47d0);return true;}
 bool title_quit_write(u32 p,u32 v)override{if(p<0x4e47d0||p+4>0x4e5204)return false;AnmView{common_renderer->application.data()}.put(p-0x4e47d0,v);return true;}
 bool title_quit_queue(u32 owner,u32 kind,u32 value,u32 name)override{if(owner!=0x53b1e0||name!=0x4c61a4)return false;MusicCommandQueue q;std::memcpy(q.data.data(),common_load_audio.data()+0x24f8,q.data.size());if(!q.enqueue(kind,value,"dummy"))return false;std::memcpy(common_load_audio.data()+0x24f8,q.data.data(),q.data.size());campaign_quit_events.insert(campaign_quit_events.end(),{0x4737b0,owner,kind,value,name});return true;}
}campaign_quit_control;
static bool campaign_quit_title(u32& result){if(!advance_title_quit_control(title_owner->view(),campaign_quit_control,result)){campaign_quit_failed=0x45f6e0;return false;}++campaign_quit_frames;return true;}
// Existing individually gated cleanup wrappers include the deleting-wrapper
// free. The aggregate calls the destructor first and performs that same free
// afterward. Suppress only this one owner release in the wrapper's storage.
struct CampaignQuitStorage:GameOwnerServices {
 u32 deferred=0;
 bool reserve_game_owner(u32 p,u32 n)override{return common_load_storage.reserve_game_owner(p,n);}
 bool allocate_game_storage(u32 n,u32& p)override{return common_load_storage.allocate_game_storage(n,p);}
 bool release_game_storage(u32 p)override{return p==deferred||common_load_storage.release_game_storage(p);}
 bool request_game_resource(u32 slot,const char* name,u32& p)override{return common_load_storage.request_game_resource(slot,name,p);}
 bool read_player_shots(std::vector<u8>& out)override{return common_load_storage.read_player_shots(out);}
 u8 game_allocation_fill()const override{return common_load_storage.game_allocation_fill();}
}campaign_quit_storage;
struct CampaignQuitCommon:CommonCleanupHost {
 bool wait_common_worker(u32 handle,u32 ms,u32& status)override{if(handle!=0x77770002||ms!=200)return false;campaign_quit_events.insert(campaign_quit_events.end(),{1,handle,ms});status=0;return true;}
 bool sleep_common_worker(u32)override{return false;}
 bool close_common_worker(u32 handle)override{if(handle!=0x77770002)return false;campaign_quit_events.insert(campaign_quit_events.end(),{2,handle});return true;}
 bool common_save_directory(bool restore)override{return title_platform.save_directory(restore);}
 bool open_common_save(i32& status,u32& handle)override{return title_platform.open_save_file(status,handle);}
 bool write_common_save(u32 handle,const u8* p,u32 n,u32& written)override{return title_platform.write_save_file_bytes(handle,p,n,written);}
 bool close_common_save(u32 handle)override{return title_platform.close_save_file(handle);}
 bool common_save_error()override{return title_platform.save_file_error();}
}campaign_quit_common;
struct CampaignQuitCleanup:ApplicationOwnerCleanupHost {
 bool cleanup_global_read(u32 p,u32& value)override{
  switch(p){case 0x53b150:value=campaign_quit_signal;break;case 0x4e6a5c:value=title_root_globals.root;break;case 0x4e6bb4:value=title_owner->global_owner;break;case 0x4e6b70:value=common_owner->global_owner;break;case 0x4e6a40:value=common_auxiliary->effects_owner;break;case 0x4e6b60:value=campaign_manual_owner;break;case 0x4e6bc8:value=campaign_dialog_owner;break;case 0x4e6b68:value=title_cheat->global_owner;break;case 0x4e6b80:value=day1_notice_globals.owner;break;case 0x4e6bc4:value=campaign_achievement_owner;break;default:value=title_root_load_global(p);break;}return true;
 }
 bool cleanup_global_write(u32 p,u32 value)override{if(p!=0x53b150)return false;campaign_quit_signal=value;return true;}
 bool cleanup_destructor(u32 entry,u32 owner)override{
  campaign_quit_failed=entry;campaign_quit_events.insert(campaign_quit_events.end(),{entry,owner});campaign_quit_storage.deferred=owner;
  if(entry==0x467a30)return campaign_achievement_cleanup(owner);
  if(entry==0x45f370&&owner==GameTitleRuntime::self){auto& b=*title_bindings;TitleLoadBindings local{b.title,b.common,b.frames,b.cheat,b.resources,campaign_quit_storage,b.save,b.application,b.globals,b.equipment,b.saved_equipment,b.alternate,b.global_538de4};local.loaded_save=b.loaded_save;return destroy_title(local,campaign_quit_worker);}
  if(entry==0x443280&&owner==GameCommonRuntime::self){auto& b=*common_load_bindings;CommonLoadBindings local{b.common,b.frames,b.ascii,b.auxiliary,b.trophies,b.save,b.save_runtime,b.resources,campaign_quit_storage,b.application,b.audio,b.gameplay,b.equipment,b.saved_equipment};local.save_owner=b.save_owner;local.loaded_save=b.loaded_save;const bool ok=destroy_common(local,campaign_quit_common);b.save_owner=local.save_owner;return ok;}
  // Main-menu domain has no Root, dialogs or additional scene owners. Reject
  // any unexpected live object rather than silently skip its destructor.
  return false;
 }
 bool cleanup_free(u32 owner)override{campaign_quit_events.insert(campaign_quit_events.end(),{0x48a6e8,owner});campaign_quit_storage.deferred=0;if(campaign_achievement_storage.count(owner))return campaign_achievement_free(owner);return common_load_storage.release_game_storage(owner);}
}campaign_quit_cleanup;
struct CampaignQuitState:ApplicationStateServices {
 bool lock_application_state(bool)override{return false;}
 bool application_root_mode(u32&)override{return false;}
 bool application_state_call(u32 entry,u32 owner,u32 argument,u32& result)override{result=0;if(entry==0x443c30)return cleanup_application_owners(campaign_quit_cleanup);if(entry==0x4073d0&&owner==0&&argument==5){campaign_quit_events.insert(campaign_quit_events.end(),{entry,argument});return true;}return false;}
}campaign_quit_state;
struct CampaignQuitWrite:ExitConfigurationWriteHost {
 bool exit_configuration_write(const u8* path,u32 n,AnmView in,u32 bytes,u32& result)override{constexpr u8 expected[]="th143.cfg";if(n!=sizeof expected||std::memcmp(path,expected,n))return false;campaign_quit_events.insert(campaign_quit_events.end(),{0x403040,bytes});return campaign_configuration.write_configuration(0x4c86b8,in,bytes,result);}
}campaign_quit_write;
API(campaign_quit_finish)u32 campaign_quit_finish(){
 if(campaign_quit_closed)return 1;auto app=AnmView{common_renderer->application.data()};if(app.get(0x6ec)!=3||title_root_globals.root||!title_owner->global_owner)return 0;
 ApplicationStateGlobals g{};i32 result;if(!transition_application_state(app,g,campaign_quit_state,result)||result!=4)return 0;
 if(!campaign_finish_shutdown_tail())return 0;campaign_quit_failed=0;campaign_quit_closed=1;campaign_cold_title_active=false;return 1;
}
API(campaign_quit_diagnostic)u32 campaign_quit_diagnostic(u32 i){const u32 v[]={campaign_quit_failed,campaign_quit_frames,campaign_quit_closed,campaign_quit_signal,title_owner->global_owner,common_owner->global_owner,game_ascii->global_owner,common_auxiliary->effects_owner,title_cheat->global_owner,common_load_bindings->save_owner,u32(campaign_quit_events.size())};return i<11?v[i]:0;}
API(campaign_quit_events_data)const u32* campaign_quit_events_data(){return campaign_quit_events.data();}
API(campaign_quit_events_words)u32 campaign_quit_events_words(){return campaign_quit_events.size();}

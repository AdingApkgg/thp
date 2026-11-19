// Native-gated replay initializer/frame/end-entry over the retained game owners.
static u32 campaign_replay_playback_last_read=0,campaign_replay_playback_last_write=0,campaign_replay_playback_last_call=0;
static u32 campaign_replay_playback_failed=0,campaign_replay_playback_factories=0,campaign_replay_playback_frames=0,campaign_replay_playback_ends=0;
static bool campaign_replay_handoff_call(u32 entry,u32 owner,std::initializer_list<u32> args,u32& result){
 result=0;const auto a=args.begin();
 if(entry==0x41af40)return owner==0&&args.size()==3&&a[0]==0&&a[1]==0&&a[2]==0&&natural_first_host.first_start_transition(result);
 if(entry==0x484320)return args.size()==2&&natural_first_host.first_start_signal(a[0],signed_word(a[1]));
 if(entry==0x41ce10)return args.size()==2&&natural_first_host.first_start_ascii(a[0],a[1]);
 if(entry==0x44b7b0)return owner==0x4e46f0&&args.size()==1&&initialize_application_game_mode({title_scene_handoff_game.data()},signed_word(a[0]),result);
 if(entry==0x4674b0)return args.size()==1&&set_application_scene_flags({title_scene_handoff_game.data()},a[0],result);
 return false;
}
struct CampaignReplayCleanup:TitleReplayCleanupHost {bool cleanup_title_replay(u32 token)override{return campaign_replay_menu_recording_destroy(token);}}campaign_replay_cleanup;
static TitleReplayCleanupHost* campaign_replay_cleanup_host(){return &campaign_replay_cleanup;}
struct CampaignReplayPlayback:GameManagerReplayInitHost,GameManagerReplayFrameHost,GameReplayEndEntryHost,GameRootReplayInputHost {
 bool read(u32 p,void* out,u32 n){campaign_replay_playback_last_read=p;
  auto copy=[&](u32 base,const void* data,u32 bytes){if(p<base||std::uint64_t(p)+n>std::uint64_t(base)+bytes)return false;std::memcpy(out,static_cast<const u8*>(data)+p-base,n);return true;};
  std::array<u8,0xc4> game{};std::memcpy(game.data(),title_scene_handoff_game.data(),game.size());std::memcpy(game.data(),title_root_game.game_state.data(),160);for(const auto&[a,v]:title_root_load_words)if(a>=0x4e4790&&a+4<=0x4e47b4)AnmView{game.data()}.put(a-0x4e46f0,v);AnmView{game.data()}.put(0xac,title_root_game.scene);AnmView{game.data()}.put(0xc0,title_root_game.game_flags);
  if(copy(0x4e46f0,game.data(),game.size())||copy(0x4e69e8,&title_root_game.random,sizeof(Rng))||copy(0x4e6b98,&title_root_game.current,4)||copy(0x4e6a5c,&title_root_globals.root,4)||copy(0x53b150,&common_texture_application_globals.presentation,4))return true;
  const u32 hud=title_root_hud?title_root_hud->globals.owner:0,resource=AnmView{common_renderer->application.data()}.get(0x71c);if(copy(0x4e6a54,&hud,4)||copy(0x4e4eec,&resource,4))return true;
  const u32 rate=word(world->rate);if(copy(0x4e40b0,&rate,4))return true;
  if(copy(0x6e004000,title_root_state.data.data(),RootState::bytes))return true;
  if(owners->read(p,out,n)||title_root_load_read(p,out,n)||campaign_replay_services.title_option_read(p,out,n))return true;
  return false;
 }
 bool write(u32 p,const void* in,u32 n){campaign_replay_playback_last_write=p;
  auto copy=[&](u32 base,void* data,u32 bytes){if(p<base||std::uint64_t(p)+n>std::uint64_t(base)+bytes)return false;std::memcpy(static_cast<u8*>(data)+p-base,in,n);return true;};
  if(copy(0x4e46f0,title_root_game.game_state.data(),160)||copy(0x4e69e8,&title_root_game.random,sizeof(Rng))||copy(0x4e6b98,&title_root_game.current,4)||copy(0x4e47b0,&title_root_game.game_flags,4)||copy(0x53b150,&common_texture_application_globals.presentation,4)||copy(0x6e004000,title_root_state.data.data(),RootState::bytes))return true;
  if(p==0x4e40b0&&n==4){u32 rate;std::memcpy(&rate,in,4);world->rate=real(rate);return true;}
  if(p>=0x4e4790&&std::uint64_t(p)+n<=0x4e47b0&&n==4){u32 value;std::memcpy(&value,in,4);title_root_load_words[p]=value;if(p==0x4e479c)title_root_game.scene=value;return true;}
  return owners->write(p,in,n)||campaign_replay_services.title_option_write(p,in,n);
 }
 bool read_manager_memory(u32 p,void* out,u32 n)override{return read(p,out,n);}bool write_manager_memory(u32 p,const void* in,u32 n)override{return write(p,in,n);}
 bool release_manager_storage(u32 p)override{return campaign_replay_services.replay_free(p);}bool remove_manager_callback(u32 p)override{return frames->scheduler.remove(p,campaign_manual_services);}
 bool allocate_manager_storage(u32 n,u32& token)override{if(!title_root_ready->allocate_game_storage(n,token)||!token)return false;owners->storage.push_back({token,std::vector<u8>(std::max(1u,n),u8(fill))});return true;}
 bool register_manager_callback(u32 entry,i32 priority,bool draw,u32 owner,u32& token)override{const u32 flags=(u32(u8(fill))*0x01010101u&~3u)|1;return allocate_manager_storage(0x28,token)&&frames->register_callback(token,entry,owner,priority,draw,flags);}
 bool load_manager_replay(u32 name,u32& status)override{if(name!=0x4e6a60)return false;return load_game_replay_file(owners->input.manager,campaign_replay_decoder,campaign_replay_filename.data(),campaign_replay_filename.size(),campaign_replay_services,status);}
 bool create_root_replay_input(u32 mode,GameManagerInitGlobals& g,u32& result)override{
  campaign_replay_playback_failed=0x454740;if(mode!=1||(&g!=&title_root_game)||(owners->created&4)||!title_root_ready->reserve_game_owner(GameOwnerRuntime::input_self,GameManagerState::bytes))return false;
  owners->created|=4;owners->input.manager.data.fill(0);u32 status;if(!initialize_game_manager_replay(owners->input.manager,GameOwnerRuntime::input_self,1,0x4e6a60,*this,status))return false;
  if(status){if(!game_manager_cleanup(owners->input.manager,GameOwnerRuntime::input_self,g.current,static_cast<GameManagerReplayInitHost&>(*this))||!title_root_ready->release_game_storage(GameOwnerRuntime::input_self))return false;owners->created&=~4u;result=0;return true;}
  // The same decoded allocation must be visible to4554b0 through GameOwnerRuntime.
  for(u32 at:{0x18,0x64}){const u32 token=owners->input.manager.view().get(at);auto it=campaign_replay_buffers.find(token);if(it==campaign_replay_buffers.end())return false;it->second.resize(it->second.size()+16,u8(fill));owners->storage.push_back({token,std::move(it->second)});campaign_replay_buffers.erase(it);}
  frames->input=&owners->input;result=GameOwnerRuntime::input_self;++campaign_replay_playback_factories;campaign_replay_playback_failed=0;return true;
 }
 bool end_manager_replay()override{campaign_replay_playback_failed=0x448490;u32 result;if(!title_root_menu||!enter_game_replay_end(title_root_menu->menu.view(),*this,result))return false;++campaign_replay_playback_ends;campaign_replay_playback_failed=0;return true;}
 bool replay_end_read(u32 p,void* out,u32 n)override{return read(p,out,n);}bool replay_end_write(u32 p,const void* in,u32 n)override{return write(p,in,n);}
 bool replay_end_call(u32 entry,u32 owner,std::initializer_list<u32> args,u32& result)override{campaign_replay_playback_last_call=entry;const auto a=args.begin();result=0;if(entry==0x483f00){if(args.size()!=6||a[1]||a[2]||a[3]!=0xffffffff||a[4]!=4||a[5])return false;return common_pool_overlay.create(*world,owner,signed_word(a[0]),nullptr,0,-1,4,result);}if(entry==0x484320)return args.size()==2&&signal_animation(*world,a[0],signed_word(a[1]),false);if(entry==0x433f70)return args.size()==0&&title_gameplay_menu_host.pause_audio();return false;}
}campaign_replay_playback;
static GameRootReplayInputHost& campaign_replay_input_host(){return campaign_replay_playback;}
static bool campaign_replay_playback_frame(u32 owner,u32& result){campaign_replay_playback_failed=0x455430;result=1;if(owner!=GameOwnerRuntime::input_self||!advance_game_manager_replay(owners->input.manager,owners->input.input.keyboard,title_root_globals.root!=0,campaign_replay_playback))return false;++campaign_replay_playback_frames;campaign_replay_playback_failed=0;return true;}
API(campaign_replay_root_prepare)void campaign_replay_root_prepare(){title_root_prepare();title_activation_globals.return_mode=campaign_replay_return;}
API(campaign_replay_root_run)i32 campaign_replay_root_run(){return title_root_run();}
API(campaign_replay_playback_diagnostic)u32 campaign_replay_playback_diagnostic(u32 i){auto g=owners->input.manager.view();const u32 v[]={campaign_replay_playback_failed,campaign_replay_playback_factories,campaign_replay_playback_frames,campaign_replay_playback_ends,title_root_state.view().get(0x94),g.get(0x10),g.get(0x50),g.get(0x6c),g.get(0x74),owners->input.held(),owners->input.fresh(),g.get(0x68),title_root_game.random.seed,title_root_game.random.calls,campaign_replay_playback_last_read,campaign_replay_playback_last_write,campaign_replay_playback_last_call};return i<17?v[i]:0;}

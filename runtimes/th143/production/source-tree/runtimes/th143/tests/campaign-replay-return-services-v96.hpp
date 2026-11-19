static u32 campaign_replay_return_activations=0;
struct CampaignReplayReturnServices:CampaignReplayServices {
 bool title_option_read(u32 p,void* out,u32 n)override{
  if(n==4){u32 value=0;bool found=true;switch(p){case 0x4e6bb0:value=title_activation_globals.return_mode;break;case 0x4e47b0:value=title_activation_globals.startup_flags;break;case 0x4e46fc:value=title_activation_globals.game_state;break;case 0x4e4798:value=title_activation_globals.cached_game_state;break;case 0x4e6b68:value=title_cheat->global_owner;break;case 0x4e6b80:value=title_activation_globals.trophy_owner;break;default:found=false;}if(found){std::memcpy(out,&value,4);return true;}auto cb=frames->scheduler.at(p);if(cb.data){std::memcpy(out,cb.data,4);return true;}}
  if(p>=GameCheatRuntime::self&&std::uint64_t(p)+n<=std::uint64_t(GameCheatRuntime::self)+title_cheat->data.size()){std::memcpy(out,title_cheat->data.data()+p-GameCheatRuntime::self,n);return true;}
  return CampaignReplayServices::title_option_read(p,out,n);
 }
 bool title_option_write(u32 p,const void* in,u32 n)override{
  if(n==4){u32 value;std::memcpy(&value,in,4);switch(p){case 0x4e6bb0:title_activation_globals.return_mode=value;campaign_replay_return=value;return true;case 0x4e47b0:title_activation_globals.startup_flags=value;return true;case 0x4e46fc:title_activation_globals.game_state=value;return true;default:break;}auto cb=frames->scheduler.at(p);if(cb.data){std::memcpy(cb.data,in,4);return true;}}
  return CampaignReplayServices::title_option_write(p,in,n);
 }
 bool title_option_call(u32 entry,u32 owner,std::initializer_list<u32> args,u32& result)override{
  result=0;const auto a=args.begin();if(entry==0x467520){if(owner!=0x4e49a0||args.size())return false;result=world->find(AnmView{common_renderer->application.data()}.get(0x1d0)).data!=nullptr;return true;}
  if(entry==0x41cd10){if(args.size())return false;auto ascii=game_ascii->view();if(!signal_animation(*world,ascii.get(0x191ec),1,false))return false;ascii.put(0x191ec,0);return true;}
  if(entry==0x484320){if(args.size()!=2)return false;return signal_animation(*world,a[0],signed_word(a[1]),false);}
  if(entry==0x484590){if(owner!=0x72000000||args.size()!=1)return false;for(u32 head:{world->instances.registry.primary_head,world->instances.registry.secondary_head})for(u32 node=head,budget=0;node;){auto it=world->instances.registry.nodes.find(node-0x570);if(it==world->instances.registry.nodes.end()||++budget>1000000)return false;auto vm=it->second;if(vm.get(0x30)==a[0])vm.put(0x1c,vm.get(0x1c)|0x20u);node=vm.get(0x574);}return true;}
  if(entry==0x444660||entry==0x4446e0){if(args.size()!=2)return false;MusicCommandQueue queue;std::memcpy(queue.data.data(),common_load_audio.data()+0x24f8,queue.data.size());MusicScene music;const bool ok=entry==0x444660?a[1]==0x4c7b2c&&music.load(queue,"th143_01"):a[0]==0&&a[1]==0&&queue.start(*common_save,0,0,AnmView{common_renderer->application.data()}.get(0x20c));if(!ok)return false;std::memcpy(common_load_audio.data()+0x24f8,queue.data.data(),queue.data.size());return true;}
  if(entry==0x44b7b0){if(owner!=0x4e46f0||args.size()!=1)return false;auto g=AnmView{title_scene_handoff_game.data()};g.put(12,title_activation_globals.game_state);g.put(0xc0,title_activation_globals.startup_flags);if(!initialize_application_game_mode(g,signed_word(a[0]),result))return false;title_activation_globals.game_state=g.get(12);title_activation_globals.startup_flags=g.get(0xc0);return true;}
  if(entry==0x4650c0)return owner==GameTitleRuntime::self&&args.size()==0&&advance_title_replay_control_v2(title_owner->view(),owner,*this,result,false);
  return CampaignReplayServices::title_option_call(entry,owner,args,result);
 }
}campaign_replay_return_services;
static bool campaign_replay_return_title(u32& result){if(!activate_returned_title_replay(title_owner->view(),GameTitleRuntime::self,campaign_replay_return_services,result))return false;if(campaign_replay_pending){if(!load_title_replay_list(title_owner->view(),campaign_replay_services))return false;campaign_replay_pending=0;++campaign_replay_counts[2];}++campaign_replay_return_activations;campaign_replay_failed=0;return world->synchronize_resources();}

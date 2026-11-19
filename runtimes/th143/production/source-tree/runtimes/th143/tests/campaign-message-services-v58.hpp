// FreshV20 composition of independently checked MSG services.
static bool campaign_message_storage(u32 token,AnmView& out){for(auto& s:title_root_messages)if(s.token==token&&s.bytes.size()==0x1b8){out={s.bytes.data()};return true;}out={nullptr};return false;}
struct CampaignMessageServices:HudScriptMessageFactoryHost,HudScriptMessageInitHost,HudMessageFlowHost,HudMessagePortraitCreateHost,HudMessagePortraitControlHost,HudMessageTextHost,HudMessageWindowHost,HudMessageTextCallbackHost,HudMessageDialogInstructionHost {
 u32 failed=0,opcode=0,last_pc=0;
 bool timer_rate(u32 p,float& r)override{return world->timer_rate(p,r);}
 bool read(u32 p,void* out,u32 n){return title_root_load_read(p,out,n)||world->read(p,out,n);}
 bool message_factory_read(u32 p,u32& out)override{return read(p,&out,4);}
 bool message_factory_destroy(u32 p)override{AnmView s;if(!campaign_message_storage(p,s)||!cleanup_hud_message(s,*world))return false;return campaign_message_release(p,false);}
 bool message_factory_allocate(u32 n,u32& p,AnmView& out)override{if(n!=0x1b8||!common_load_storage.allocate_game_storage(n,p))return false;title_root_messages.push_back({p,std::vector<u8>(n,u8(fill))});out={title_root_messages.back().bytes.data()};return true;}
 bool message_factory_construct(u32,AnmView s,u32 code)override{return initialize_hud_script_message(s,code,AnmView{common_renderer->application.data()}.get(0x71c),*this);}
 bool message_create_text(u32 r,i32 script,u32& h)override{return common_pool_overlay.create(*world,r,script,nullptr,0,-1,4,h);}
 bool message_signal_text(u32 h,i32 signal)override{return signal_animation(*world,h,signal,false);}
 AnmView message_text_vm(u32 h)override{return world->find(h);}
 bool message_read(u32 p,void* out,u32 n)override{return read(p,out,n);}
 bool message_play_sound(i32 id)override{return title_start_audio.request(id,false,0);}
 bool message_signal_immediate(u32 h,i32 signal)override{return signal_animation(*world,h,signal,true);}
 AnmView message_visual(u32 h)override{return world->find(h);}
 bool message_dialog_create()override{return campaign_dialog_create();}
 AnmView message_dialog_current()override{return campaign_dialog_view(campaign_dialog_owner);}
 bool message_dialog_read(u32 p,void* out,u32 n)override{return campaign_dialog_read(p,out,n);}
 bool message_external_instruction(AnmView s,u8 op,const u8* payload,u32 n)override{
  opcode=op;last_pc=s.get(0x158);failed=op;
  if(op==1||op==2||op==20||op==31){u32 player;if(!read(0x4e46f0,&player,4))return false;return create_hud_message_portrait(s,op,payload,n,{player,owners->player.get(0x10),title_scene_handoff_descriptor,GameEnemyRuntime::self},*this);}
  if(op==4||op==5||op==6||op==7||op==8||op==18||op==23||op==24||op==25||op==32)return execute_hud_message_portrait_control(s,op,*this);
  if(op==17)return execute_hud_message_text(s,payload,n,*this);
  if(op==33)return execute_hud_message_dialog_instruction(s,*this);
  return false;
 }
 bool message_indicator(AnmView s,AnmView,i32& result)override{result=0;return update_hud_message_indicator_position(s,world->viewport.scale,*this);}
 bool portrait_read_word(u32 p,u32& out)override{return read(p,&out,4);}
 bool portrait_create(u32 r,i32 script,u32& h)override{return common_pool_overlay.create(*world,r,script,nullptr,0,-1,4,h);}
 bool portrait_control_read(u32 p,u32& out)override{return read(p,&out,4);}
 bool portrait_control_signal(u32 h,i32 signal,bool immediate)override{return signal_animation(*world,h,signal,immediate);}
 AnmView portrait_control_visual(u32 h)override{return world->find(h);}
 bool portrait_control_discard_indicator(AnmView s)override{return retire_hud_message_window(s,*this);}
 AnmView message_text_resolve(u32& h)override{auto v=world->find(h);if(!v.data)h=0;return v;}
 bool message_text_draw(AnmView v,u32 fg,u32 outline,i32 kind,i32 x,i32 pitch,const u8* b,u32 n)override{return title_text_runtime&&anm_positioned_text_literal(v,boot_raster,fg,outline,kind,x,pitch,b,n,*title_text_runtime);}
 bool message_text_signal(u32 h,i32 signal,bool immediate)override{return signal_animation(*world,h,signal,immediate);}
 bool message_text_position(u32& h,const std::array<float,3>& p)override{auto v=world->find(h);if(!v.data){h=0;return true;}for(u32 i=0;i<3;++i)v.put(0x59c+i*4,word(p[i]));return true;}
 bool message_text_window(AnmView s,i32 index,float x,float y,float width)override{return create_hud_message_window(s,title_root_hud->view().get(0x2ac),index,x,y,width,*this);}
 bool message_text_width(AnmView s,i32 index,float width)override{return resize_hud_message_window(s,index,width,*this);}
 AnmView message_window_visual(u32 h)override{return world->find(h);}
 AnmView message_window_state(u32 p)override{return world->state(p);}
 bool message_window_read(u32 p,u32& v)override{return world->read(p,&v,4);}
 bool message_window_create(u32 r,i32 script,const std::array<float,3>& p,u32& h)override{return common_pool_overlay.create(*world,r,script,&p,0,-1,4,h);}
 AnmView message_window_child(AnmView v,i32 script)override{return find_animation_child(*world,v,script);}
 AnmView message_callback_visual(u32 h)override{return world->find(h);}
 AnmView message_callback_child(AnmView v,i32 script)override{return find_animation_child(*world,v,script);}
 bool message_callback_transform(AnmView v,std::array<float,3>& p)override{return anm_position(v,world->viewport,*world,p);}
}campaign_message_services;
static bool campaign_message_release(u32 token,bool array){
 for(auto i=title_root_messages.begin();i!=title_root_messages.end();++i)if(i->token==token){title_root_messages.erase(i);world->releases.insert(world->releases.end(),{array?1u:2u,token});const auto previous=common_load_storage_release_observer;common_load_storage_release_observer=nullptr;const bool ok=common_load_storage.release_game_storage(token);common_load_storage_release_observer=previous;return ok;}return false;
}
static bool campaign_message_create(i32 id){campaign_message_services.failed=0;if(id==-1||id==-2||id==-3){++campaign_special_message_services.calls;campaign_special_message_services.last_id=u32(id);return create_hud_special_message(title_root_state.view(),title_root_game.game_flags,id,campaign_special_message_services);}return create_hud_script_message(title_root_hud->view(),title_root_state.view(),title_root_game.game_flags,id,campaign_message_services);}
static bool campaign_message_update(u32 token,i32& result){
 AnmView s;if(!campaign_message_storage(token,s))return false;auto input=title_device.view();campaign_message_services.failed=0;campaign_message_services.last_pc=s.get(0x158);
 return step_hud_message_flow(s,{input.get(0xc),input.get(0),input.get(0x114),input.get(0x138)},campaign_message_services,result);
}
static bool campaign_message_destroy(u32 token){return campaign_message_services.message_factory_destroy(token);}
namespace th143 {bool campaign_hud_message_draw(u32 entry,AnmView text){if(entry!=0x430740)return false;AnmView s;if(!campaign_message_storage(title_root_hud->view().get(0x198),s))return false;return position_hud_message_text(s,text,world->viewport.scale,campaign_message_services);}}
API(campaign_message_diagnostic)u32 campaign_message_diagnostic(u32 i){switch(i){case 0:return campaign_message_services.failed;case 1:return campaign_message_services.opcode;case 2:return campaign_message_services.last_pc;case 3:return title_root_hud->view().get(0x198);default:return 0;}}

API(campaign_message_storage_count) u32 campaign_message_storage_count(){return title_root_messages.size();}

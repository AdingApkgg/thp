// Experimental continuous composition of independently checked notice bodies.
// Worker scheduling remains an explicit cooperative OS service, mirrored by
// the fresh original producer. This file is not an acceptance receipt.
#include "../src/NoticeLifecycle.hpp"
#include "../src/NoticeWorkers.hpp"
#include "../src/NoticeUpdate.hpp"
#include "../src/PendingNoticeQueue.hpp"
#include "../src/NoticeResultsGate.hpp"
static NoticeLifecycleGlobals day1_notice_globals;
static std::map<u32,std::vector<u8>> day1_notice_storage;
static u32 day1_notice_pending_worker=0,day1_notice_thread_cursor=0,day1_notice_failure=0;
static AnmView day1_notice_view(){auto i=day1_notice_storage.find(day1_notice_globals.owner);return {i==day1_notice_storage.end()?nullptr:i->second.data()};}
struct Day1NoticePreloadDevice:TitlePreviewImageDevice {
 std::vector<u32> requests;
 bool preload_preview_texture(u32 token)override{if(!common_texture_resources->textures.images.count(token))return false;requests.push_back(token);return true;}
}day1_notice_preload_device;
struct Day1NoticeWorkerPlatform:RootFactoryHost {
 BackgroundWorker* current=nullptr;
 void publish(){if(current)std::memcpy(common_renderer->application.data()+0x98c,current->data.data(),current->data.size());}
 bool allocate_root(u32&)override{return false;}bool evict_managed_textures()override{return false;}
 bool wait_worker(u32 h,u32 ms,u32& result)override{publish();if(ms!=200||day1_notice_pending_worker)return false;title_scene_event({1,h,ms});result=0;return true;}
 bool sleep_worker(u32)override{return false;}
 bool close_worker(u32 h)override{publish();title_scene_event({2,h});return true;}
 bool launch_worker(u32 entry,u32 argument,u32 flags,u32& id,u32& handle)override{publish();if(argument||flags||day1_notice_pending_worker)return false;day1_notice_pending_worker=entry;++day1_notice_thread_cursor;id=0x11223400+day1_notice_thread_cursor;handle=0x77770100+day1_notice_thread_cursor;return true;}
}day1_notice_worker_platform;
struct Day1NoticeServices:NoticeLifecycleHost,NoticeWorkerHost,NoticeUpdateHost,SchedulerHost {
 bool invoke(u32,u32,u32&)override{return false;}
 bool release_callback(u32 p)override{return common_load_storage.release_game_storage(p);}
 bool timer_rate(u32 p,float& v)override{return world->timer_rate(p,v);}
 bool notice_allocate(u32 n,u32& token,AnmView& out)override{day1_notice_failure=1;if(!common_load_storage.allocate_game_storage(n,token))return false;auto& b=day1_notice_storage[token];b.assign(n,u8(fill));out={b.data()};return true;}
 bool notice_callback(u32 entry,u32& token,AnmView& out)override{day1_notice_failure=2;if(!common_load_storage.allocate_game_storage(0x28,token)||!frames->scheduler.create(token,entry,u8(fill)))return false;out=frames->scheduler.at(token);return true;}
 bool notice_register(u32 p,i32 priority,bool draw)override{day1_notice_failure=3;u32 ignored;return frames->scheduler.add(p,priority,draw,*this,ignored);}
 bool notice_start_worker(u32 entry)override{
  day1_notice_failure=4;BackgroundWorker worker;std::memcpy(worker.data.data(),common_renderer->application.data()+0x98c,worker.data.size());day1_notice_worker_platform.current=&worker;
  if(!stop_background_worker(worker,day1_notice_worker_platform)){day1_notice_worker_platform.current=nullptr;return false;}
  auto w=worker.view();w.put(24,entry);w.put(16,1);w.put(12,0);u32 id=w.get(8),handle;
  const bool okay=day1_notice_worker_platform.launch_worker(entry,0,0,id,handle);if(okay){w.put(8,id);w.put(4,handle);}day1_notice_worker_platform.publish();day1_notice_worker_platform.current=nullptr;return okay;
 }
 bool notice_remove_callback(u32 p)override{day1_notice_failure=5;return frames->scheduler.remove(p,*this);}
 bool notice_destroy_resource(u32 p)override{day1_notice_failure=6;return cleanup_anm_resource(p,{world->instances.registry.primary_head,world->instances.registry.secondary_head},*world);}
 bool notice_release(u32 p)override{day1_notice_failure=7;if(day1_notice_storage.count(p))return common_load_storage.release_game_storage(p);return world->release_enemy_storage(p,false);}
 bool notice_resource(u32 slot,const char* name,u32& token)override{day1_notice_failure=8;u32 previous;if(slot>=30||!world->read(0x72bc7b0c+slot*4,&previous,4)||!common_load_storage.request_game_resource(slot,name,token))return false;if(token&&!previous){for(u32 budget=0;;++budget){if(AnmView{common_renderer->application.data()}.get(0x724)&0x180)break;i32 result;if(budget>=122880||!world->pump(result)||result)return false;u32 pending;if(!world->read(token+0x128,&pending,4))return false;if(!pending)break;}}if(slot==19)day1_notice_globals.notice_resource=token;else day1_notice_globals.congratulations_resource=token;return true;}
 bool notice_read_file(const char* name,u32& bytes,u32& token)override{day1_notice_failure=9;auto& shared=static_cast<TitleReturnedResourceWorld&>(*world);shared.next_shared_file=true;const bool okay=world->read_resource_file(name,false,token,bytes);shared.next_shared_file=false;return okay;}
 bool notice_resource_error(u32&)override{return false;}
 bool notice_read_word(u32 p,u32& v)override{return world->read(p,&v,4);}
 bool notice_texture_reset(u32 info)override{
  day1_notice_failure=10;u32 texture,surface;i32 status;if(!notice_read_word(info,texture)||!common_texture_resources->textures.surface(texture,0,surface,status)||status<0)return false;
  auto i=common_texture_resources->textures.images.find(surface);if(i==common_texture_resources->textures.images.end())return false;auto& pixels=i->second.pixels;std::memset(pixels.data.data(),0,pixels.data.size());
  return common_texture_device.texture_uploaded(surface,pixels)&&common_texture_resources->textures.release(surface);
 }
 bool notice_texture_upload(u32 info,u32 data,u32 bytes,u32 mode)override{
  day1_notice_failure=11;u32 texture,flags;if(mode!=1||!notice_read_word(info,texture)||!notice_read_word(info+20,flags))return false;flags&=~1u;
  if(!world->write(info+20,&flags,4)||!world->write(info+8,&bytes,4))return false;
  GameTitlePreviewImages images{*world,common_texture_resources->textures,common_texture_device,day1_notice_preload_device};
  const u32 kind=2;return images.upload_png(texture,data,bytes)&&world->write(info+12,&kind,4);
 }
 bool notice_free_file(u32 p)override{return world->release_enemy_storage(p,true);}
 bool notice_texture_release(u32 texture)override{day1_notice_failure=12;return day1_notice_preload_device.preload_preview_texture(texture);}
 bool notice_animation(u32 resource,i32 script,u32& handle)override{day1_notice_failure=13;return common_pool_overlay.create(*world,resource,script,nullptr,0,-1,4,handle);}
 bool notice_signal(u32 handle,i32 signal)override{day1_notice_failure=14;return signal_animation(*world,handle,signal);}
 bool notice_sound(u32 id)override{if(AnmView{common_renderer->application.data()}.get(0x6e8)==4)return title_ready_sound_host.title_sound(id);return title_start_audio.request(id,false,0);}
 bool notice_worker(u32 entry)override{return notice_start_worker(entry);}
 bool notice_format(char* out,u32 n,i32 id)override{return std::snprintf(out,n,"notice_%.2d.png",id)>=0;}
 bool notice_resource_increment(u32 p)override{day1_notice_failure=15;u32 value;if(!notice_read_word(p+0x134,value))return false;++value;++world->instances.resource_uses[p];return world->write(p+0x134,&value,4);}
 bool notice_allocate_vm(u32& token,AnmView& vm)override{return world->acquire_state(token,vm);}
 bool notice_initialize_vm(u32 resource,u32 token,i32 script)override{day1_notice_failure=16;auto* r=world->resource(resource);auto vm=world->state(token);if(!r||script<0||u32(script)>=r->templates.size()||!vm.data)return false;anm_copy_template(vm,token,{r->templates[script].data()},world->global_rate_token());return true;}
 bool notice_update_vm(u32 token)override{day1_notice_failure=17;return anm_step(world->state(token),static_cast<AnmWorld&>(*world))!=-2;}
 bool notice_register_vm(u32 token,u32& handle)override{day1_notice_failure=18;return world->instances.registry.insert(world->state(token),token,false,false,handle);}
}day1_notice_services;
static bool day1_notice_resume(){
 if(!day1_notice_pending_worker)return true;const u32 entry=day1_notice_pending_worker;day1_notice_pending_worker=0;auto s=day1_notice_view();if(!s.data)return false;u32 result;
 if(!run_notice_worker(entry,s,{common_renderer->application.data()+0x98c},frames->scheduler.at(s.get(8)),frames->scheduler.at(s.get(12)),day1_notice_services,result))return false;
 day1_notice_failure=0;return true;
}
static bool day1_notice_callback(u32 entry,u32 owner,u32& result){
 if(entry==0x4472e0){result=draw_notice();return true;}if(entry!=0x4472d0||owner!=day1_notice_globals.owner)return false;
 result=1;const bool okay=update_notice(day1_notice_view(),title_gameplay_fresh,day1_notice_services);if(okay)day1_notice_failure=0;return okay;
}
struct Day1NoticeResultsServices final:NoticeResultsHost {
 bool timer_rate(u32 p,float& value)override{return world->timer_rate(p,value);}
 bool results_create_notice(u32 id,u32& owner)override{AnmView state;if(!create_notice(id,day1_notice_globals,day1_notice_services,owner,state))return false;title_root_load_words[0x4e6b80]=owner;return true;}
 bool results_destroy_notice(u32 owner)override{
  auto state=day1_notice_view();if(!state.data||!delete_notice(state,owner,day1_notice_globals,day1_notice_services))return false;
  const u32 zero=0;if(!world->write(0x72bc7b58,&zero,4)||!world->write(0x72bc7b80,&zero,4))return false;title_root_load_words[0x4e6b80]=0;return true;
 }
}day1_notice_results_services;
static bool day1_notice_results_gate(u32& result,bool& handled){
 const bool okay=results_notice_gate(title_root_menu->menu.view(),common_save->view(),day1_notice_view(),day1_notice_globals.owner,day1_notice_results_services,handled);result=1;return okay;
}
static const u8* day1_notice_region(u32 p,u32 n){for(auto& [token,b]:day1_notice_storage)if(p>=token&&std::uint64_t(p)+n<=std::uint64_t(token)+b.size())return b.data()+p-token;return nullptr;}
API(title_notice_word) u32 title_notice_word(u32 offset){auto s=day1_notice_view();return s.data&&offset<=0x1b4?s.get(offset):0;}
API(title_notice_owner) u32 title_notice_owner(){return day1_notice_globals.owner;}
API(title_notice_failed) u32 title_notice_failed(){return day1_notice_failure;}

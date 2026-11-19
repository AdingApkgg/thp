#include "../src/AchievementUnlockNov14.hpp"
#include "../src/AchievementQueueLifecycleNov14.hpp"
#include "../src/AchievementQueueUpdateNov14.hpp"
static u32 campaign_achievement_owner=0,campaign_achievement_failed=0,campaign_achievement_updates=0,campaign_achievement_notices=0,campaign_achievement_unlocked=0;
static std::map<u32,std::vector<u8>> campaign_achievement_storage;
static std::array<u8,256> campaign_achievement_scratch{};
static std::vector<std::string> campaign_achievement_texts;
static AnmView campaign_achievement_view(u32 owner){auto i=campaign_achievement_storage.find(owner);return {i==campaign_achievement_storage.end()?nullptr:i->second.data()};}
struct CampaignAchievementServices:AchievementUnlockHost,AchievementQueueUpdateHost,SchedulerHost {
 bool invoke(u32,u32,u32&)override{return false;}
 bool release_callback(u32 p)override{return common_load_storage.release_game_storage(p);}
 bool memory(u32 p,void* bytes,u32 n,bool write){
  for(auto& [token,b]:campaign_achievement_storage)if(p>=token&&std::uint64_t(p)+n<=std::uint64_t(token)+b.size()){if(write)std::memcpy(b.data()+p-token,bytes,n);else std::memcpy(bytes,b.data()+p-token,n);return true;}
  for(auto& [token,b]:frames->scheduler.records)if(p>=token&&std::uint64_t(p)+n<=std::uint64_t(token)+b.size()){if(write)std::memcpy(b.data()+p-token,bytes,n);else std::memcpy(bytes,b.data()+p-token,n);return true;}
  for(auto& [token,v]:world->instances.registry.nodes)if(p>=token&&std::uint64_t(p)+n<=std::uint64_t(token)+12){if(write)std::memcpy(v.data+p-token,bytes,n);else std::memcpy(bytes,v.data+p-token,n);return true;}
  if(world->pool&&p>=world->pool->self&&std::uint64_t(p)+n<=std::uint64_t(world->pool->self)+AnmPool::bytes){auto v=world->pool->view();if(write)std::memcpy(v.data+p-world->pool->self,bytes,n);else std::memcpy(bytes,v.data+p-world->pool->self,n);return true;}
  auto i=world->state_indices.upper_bound(p);if(i!=world->state_indices.begin()){--i;if(std::uint64_t(p)+n<=std::uint64_t(i->first)+AnmView::bytes){auto v=world->state(i->first);if(write)std::memcpy(v.data+p-i->first,bytes,n);else std::memcpy(bytes,v.data+p-i->first,n);return true;}}
  return write?world->write(p,bytes,n):world->read(p,bytes,n);
 }
 bool achievement_read(u32 p,void* out,u32 n)override{
  if(p==0x538f4e&&n==1){*static_cast<u8*>(out)=0;return true;}
  if(n==4){u32 value;bool known=true;switch(p){case 0x4e6bc4:value=campaign_achievement_owner;break;case 0x4e69f4:value=frames->scheduler.self;break;case 0x538de8:value=world->pool->self;break;default:known=false;}if(known){std::memcpy(out,&value,4);return true;}}
  return memory(p,out,n,false);
 }
 bool achievement_write(u32 p,const void* in,u32 n)override{if(p==0x4e6bc4&&n==4){std::memcpy(&campaign_achievement_owner,in,4);return true;}return memory(p,const_cast<void*>(in),n,true);}
 bool achievement_call(u32 e,u32 owner,const u32* a,u32 count,u32& returned)override{
  campaign_achievement_failed=e;returned=0;
  if(e==0x48a697&&count==1){if(!common_load_storage.allocate_game_storage(a[0],returned))return false;if(a[0]==0x248)campaign_achievement_storage[returned].assign(a[0],u8(fill));else if(a[0]==40){if(!frames->scheduler.create(returned,0,u8(fill)))return false;}else return false;return true;}
  if(e==0x4678e0&&count==0){if(!construct_achievement_queue(campaign_achievement_view(owner),owner,*this))return false;returned=owner;return true;}
  if(e==0x467940&&count==1)return start_achievement_queue(campaign_achievement_view(owner),owner,a[0],*this,returned);
  if(e==0x467a30&&count==0)return destroy_achievement_queue(campaign_achievement_view(owner),*this);
  if(e==0x48a6e8&&count==1){if(!common_load_storage.release_game_storage(a[0]))return false;campaign_achievement_storage.erase(a[0]);return true;}
  if(e==0x482140&&count==2){
   if(a[0]!=27||a[1]!=0x4c7f20)return false;u32 previous;if(!world->read(0x72bc7b0c+27*4,&previous,4)||!common_load_storage.request_game_resource(27,"trophy.anm",returned))return false;
   if(returned&&!previous)for(u32 budget=0;;++budget){i32 status;if(budget>=122880||!world->pump(status)||status)return false;u32 pending;if(!world->read(returned+0x128,&pending,4))return false;if(!pending)break;}return true;
  }
  if(e==0x403400&&count==2)return true;
  if(e==0x401830&&count==1){return common_load_storage.allocate_game_storage(40,returned)&&frames->scheduler.create(returned,a[0],u8(fill));}
  if((e==0x4013e0||e==0x401490)&&count==2){return frames->scheduler.add(a[0],signed_word(a[1]),e==0x401490,*this,returned);}
  if(e==0x4018f0&&count==1)return frames->scheduler.remove(a[0],*this);
  return false;
 }
 bool achievement_spawn(u32 resource,u32 script,u32& handle)override{campaign_achievement_failed=0x483f00;return common_pool_overlay.create(*world,resource,i32(script),nullptr,0,-1,4,handle);}
 bool achievement_find(u32 handle,u32& vm)override{auto found=world->find(handle);vm=found.data?found.get(0x570):0;return true;}
 bool achievement_name(u32 id,u32& text)override{return lookup_trophy_name({common_trophies->data.data()},id,{campaign_achievement_scratch.data()},text);}
 bool achievement_text(u32 token,u32 format,u32 text,bool substitution)override{
  campaign_achievement_failed=0x482e40;if(!title_text_runtime)return false;auto vm=world->state(token);if(!vm.data)return false;std::vector<u8> bytes;
  if(substitution){if(format!=0x4c7f84||text!=0x541360)return false;bytes={0x81,0x77};for(u8 x:campaign_achievement_scratch){if(!x)break;bytes.push_back(x);}bytes.insert(bytes.end(),{0x81,0x78});}
  else{if(format!=0x4c7f70)return false;bytes={0x82,0xcc,0x88,0xd9,0x96,0xbc,0x82,0xf0,0x8e,0xe8,0x82,0xc9,0x93,0xfc,0x82,0xea,0x82,0xbd};}
  if(!anm_text_literal(vm,boot_raster,0x80c0c0,0,9,0,bytes.data(),bytes.size(),*title_text_runtime))return false;campaign_achievement_texts.emplace_back(bytes.begin(),bytes.end());return true;
 }
 bool achievement_sound(u32 id)override{++campaign_achievement_notices;return day1_notice_services.notice_sound(id);}
 bool achievement_rate(u32 p,float& value)override{return world->timer_rate(p,value);}
 bool achievement_destroy(u32 owner)override{u32 ignored;if(!achievement_call(0x467a30,owner,nullptr,0,ignored))return false;return achievement_call(0x48a6e8,0,&owner,1,ignored);}
}campaign_achievement_services;
static bool campaign_achievement_unlock(u32 id){
 if(!common_save||!world||!frames)return false;const bool fresh=id<70&&!common_save->data[0xeff9+id];u32 result;
 if(!unlock_achievement(common_save->view(),id,campaign_achievement_services,result))return false;
 if(fresh)++campaign_achievement_unlocked;campaign_achievement_failed=0;return true;
}
static bool campaign_achievement_callback(u32 e,u32 owner,u32& result){
 if(e==0x468110){result=1;return true;}if(e!=0x468100||owner!=campaign_achievement_owner)return false;
 if(!update_achievement_queue(campaign_achievement_view(owner),owner,campaign_achievement_services,result))return false;
 ++campaign_achievement_updates;campaign_achievement_failed=0;return world->synchronize_resources();
}
static bool campaign_achievement_cleanup(u32 owner){if(owner!=campaign_achievement_owner)return false;const bool okay=destroy_achievement_queue(campaign_achievement_view(owner),campaign_achievement_services);if(okay)campaign_achievement_failed=0;return okay;}
static bool campaign_achievement_free(u32 owner){if(!common_load_storage.release_game_storage(owner))return false;campaign_achievement_storage.erase(owner);return true;}
static const u8* campaign_achievement_region(u32 p,u32 n){for(const auto& [token,b]:campaign_achievement_storage)if(p>=token&&std::uint64_t(p)+n<=std::uint64_t(token)+b.size())return b.data()+p-token;return nullptr;}
API(campaign_achievement_diagnostic) u32 campaign_achievement_diagnostic(u32 i){auto q=campaign_achievement_view(campaign_achievement_owner);const u32 values[]={campaign_achievement_owner,campaign_achievement_failed,campaign_achievement_updates,campaign_achievement_notices,campaign_achievement_unlocked,u32(campaign_achievement_storage.size()),q.data?q.get(0x214):0,q.data?q.get(0x220):0,q.data?q.get(0x22c):0,u32(campaign_achievement_texts.size())};return i<10?values[i]:0;}
API(campaign_achievement_text_count) u32 campaign_achievement_text_count(){return campaign_achievement_texts.size();}
API(campaign_achievement_text_data) const char* campaign_achievement_text_data(u32 i){return i<campaign_achievement_texts.size()?campaign_achievement_texts[i].c_str():nullptr;}

#include "../src/EarnedAchievementRecoveryNov14.hpp"
static bool campaign_recovery_checked=false,campaign_recovery_eligible=false;
static u32 campaign_recovery_unique=0;
static std::vector<u32> campaign_recovery_requests;
static std::array<u8,SaveData::bytes> campaign_recovery_before{},campaign_recovery_after{};
static std::array<u8,8> campaign_recovery_rng_before{},campaign_recovery_rng_after{};
static bool campaign_recover_earned_achievements(){
 if(campaign_recovery_checked)return true;
 if(!common_save||!world||!frames)return false;
 campaign_recovery_checked=true;
 const auto plan=plan_earned_achievement_recovery(common_save->view());
 campaign_recovery_eligible=plan.eligible;campaign_recovery_unique=plan.uniqueScenes;
 campaign_recovery_before=common_save->data;std::memcpy(campaign_recovery_rng_before.data(),&common_gameplay,8);
 if(plan.eligible)for(u32 id:plan.requests){if(!common_load_platform.achievement(id))return false;campaign_recovery_requests.push_back(id);}
 campaign_recovery_after=common_save->data;std::memcpy(campaign_recovery_rng_after.data(),&common_gameplay,8);
 return true;
}
API(campaign_achievement_recovery_diagnostic)u32 campaign_achievement_recovery_diagnostic(u32 i){
 const u32 values[]={u32(campaign_recovery_checked),u32(campaign_recovery_eligible),campaign_recovery_unique,u32(campaign_recovery_requests.size()),u32(campaign_recovery_rng_before==campaign_recovery_rng_after)};
 return i<5?values[i]:0;
}
API(campaign_achievement_recovery_requests_data)const u32* campaign_achievement_recovery_requests_data(){return campaign_recovery_requests.data();}
API(campaign_achievement_recovery_snapshot_data)const u8* campaign_achievement_recovery_snapshot_data(u32 after){return after?campaign_recovery_after.data():campaign_recovery_before.data();}
API(campaign_achievement_recovery_rng_data)const u8* campaign_achievement_recovery_rng_data(u32 after){return after?campaign_recovery_rng_after.data():campaign_recovery_rng_before.data();}

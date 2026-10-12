#include "../../cpp/game/ItemManager.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include "../../cpp/game/EnemyState.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmEnvironment animations;static AnmResource resource;static ItemWorld world;
static std::unique_ptr<ItemManager> items;static u32 reward_count;
API(begin) i32 begin(u32 rewards,u32 flags,u32 count,u32 seed,u32 load,u32 spawn,u32 available,u32 ordinary_full,float x,float y,float z){
 if(resource.scripts.empty()){
  resource.scripts.resize(294);const AnmInstruction code[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};
  for(auto& s:resource.scripts){s.bytes.resize(sizeof code);std::memcpy(s.bytes.data(),code,sizeof code);}
  items=std::make_unique<ItemManager>(resource,animations,world,7);
 }
 items->reset();animations.rate=1;animations.visual_rng={u16(seed),0,0};animations.script_rng={54321,0,123};
 // Exhaustion is prepared through the real factory. Keep the two observed
 // slots unused, then restore counters so preparation consumes no test RNG.
 for(u32 n=0;n<4096;++n)if(items->spawn_cancel_th14(10,{0,0,0},0,0)<0)return -1;
 if(ordinary_full)for(u32 n=0;n<600;++n)if(items->spawn_ordinary_th14(1,{0,0,0},0,0)<0)return -2;
 for(u32 n=0;n<2;++n){auto& i=items->at(4695-n);i=ItemState{};i.lifetime.previous=0;}
 if(available==2)items->release_th14(items->at(4694));
 if(available)items->release_th14(items->at(4695));
 auto& ordinary=items->at(599);auto* next=ordinary.th14_free_next;ordinary=ItemState{};ordinary.lifetime.previous=0;ordinary.th14_free_next=next;
 items->th14_spawn_count=spawn;items->th14_cancel_count=load;items->th14_generation=0x12345678;reward_count=count;
 const Vec3 p{x,y,z};const float left=x+32.f,right=x-32.f,top=y+32.f,bottom=y-32.f;
 if(!rewards||left<=-192.f||right>=192.f||top<=0.f||bottom>=448.f)return 0;
 ++reward_count;return items->cancel_reward_th14(p,rewards,reward_count,flags)?0:-3;
}
API(value) u32 value(u32 n){const u32 a[]={reward_count,items->th14_spawn_count,animations.visual_rng.seed,animations.visual_rng.calls};return a[n];}
API(slot_value) u32 slot_value(u32 n,u32 k){const auto& i=items->at(n==2?599:4695-n);
 const u32 a[]={u32(i.state),u32(i.type),u32(i.display_type),float_bits(i.position.x),float_bits(i.position.y),float_bits(i.position.z),float_bits(i.velocity.x),float_bits(i.velocity.y),float_bits(i.velocity.z),u32(i.delay),i.th14_generation,u32(i.lifetime.previous),u32(i.lifetime.current),float_bits(i.lifetime.fractional)};return a[k];}

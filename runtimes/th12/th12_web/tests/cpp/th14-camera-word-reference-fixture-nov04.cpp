// Controlled mapped camera prefixes and the production Scene-only loader protocol.
#include "Stage.hpp"
#include "StagedLoaderPrototype.hpp"
#include <cstring>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
namespace {
AnmManager pub_manager;AnmResource pub_background,pub_text;u32 pub_clear=0;
std::unique_ptr<Stage> publisher;SceneCamera pub_world;u32 snapshot[sizeof(SceneCamera)/4]{};u32 reference_snapshot[6]{};
u32 progress_count=0,capture_count=0,invalid_progress=0,last_copied=0;
struct SceneActions final:prototype::StageActions{
 prototype::StagedLoader* loader=nullptr;u32 mode=0,scene_calls=0,owner_calls=0,timeline_calls=0,unexpected=0,reentries=0;
 bool retire_owner()override{++unexpected;return false;}
 bool enter_work_and_initialize()override{++unexpected;return false;}
 prototype::Work prepare_hud()override{++unexpected;return prototype::Work::Failed;}
 prototype::Work prepare_scene()override{
  ++scene_calls;
  if(mode==4){reentries+=loader->poll_scene(*this,200);reentries+=loader->pump(*this,200,-1,0);}
  if(mode==0||(mode==9&&scene_calls==1))return prototype::Work::Waiting;
  return mode==2?prototype::Work::Failed:prototype::Work::Ready;
 }
 bool publish_empty_owner()override{++owner_calls;return mode!=3;}
 prototype::Work prepare_timeline()override{++timeline_calls;++unexpected;return prototype::Work::Failed;}
} scene_actions;
prototype::StagedLoader scene_loader;u32 loader_result=0;
}
API(publication_case) u32 publication_case(u32 cut,u32 fail){
 if(cut>sizeof(SceneCamera)/4||fail>1)return ~0u;
 publisher=std::make_unique<Stage>(pub_manager,pub_background,pub_text,pub_clear,3);
 progress_count=capture_count=invalid_progress=last_copied=0;std::memset(snapshot,0,sizeof snapshot);
 for(u32 i=0;i<sizeof(SceneCamera)/4;++i){
  const u32 old_value=i==12?0xbf800000:0x3f000000+i,new_value=i==12?0:0x40000000+i;
  std::memcpy(reinterpret_cast<u8*>(&pub_world)+i*4,&old_value,4);
  std::memcpy(reinterpret_cast<u8*>(&publisher->state.camera)+i*4,&new_value,4);
 }
 publisher->active_camera=&pub_world;pub_manager.reference_positions[0]={9,8,7};
 return publisher->publish_camera([cut,fail](const Stage& owner,u32 copied){
  if(&owner!=publisher.get()||copied!=progress_count)invalid_progress=1;
  ++progress_count;last_copied=copied;
  if(copied==cut){std::memcpy(snapshot,&pub_world,sizeof pub_world);std::memcpy(reference_snapshot,&pub_manager.reference_positions[0],sizeof reference_snapshot);++capture_count;if(fail)return false;}
  return true;
 });
}
API(publication_word) u32 publication_word(u32 field){return field<sizeof(SceneCamera)/4?snapshot[field]:~0u;}
API(publication_final_word) u32 publication_final_word(u32 field){u32 v=~0u;if(field<sizeof(SceneCamera)/4)std::memcpy(&v,reinterpret_cast<const u8*>(&pub_world)+field*4,4);return v;}
API(publication_meta) u32 publication_meta(u32 field){
 const u32 words[]={progress_count,capture_count,invalid_progress,last_copied,sizeof(SceneCamera)/4,
  publisher&&!publisher->error.empty(),pub_manager.reference_positions[0].x==9};
 return field<7?words[field]:~0u;
}
API(scene_poll_case) u32 scene_poll_case(u32 mode){
 if(mode>9)return 0;scene_loader={};scene_actions={};scene_actions.loader=&scene_loader;scene_actions.mode=mode;
 scene_loader.phase=mode==5?prototype::LoadPhase::Hud:mode==7?prototype::LoadPhase::Aborted:mode==8?prototype::LoadPhase::Ready:prototype::LoadPhase::Scene;
 scene_loader.has_sample=true;scene_loader.last_sample=100;loader_result=scene_loader.poll_scene(scene_actions,mode==6?99:200);
 if(mode==9)loader_result=loader_result&&scene_loader.poll_scene(scene_actions,201);return 1;
}
API(scene_poll_word) u32 scene_poll_word(u32 field){
 const u32 words[]={loader_result,u32(scene_loader.phase),scene_actions.scene_calls,scene_actions.owner_calls,
  scene_actions.timeline_calls,scene_actions.unexpected,scene_actions.reentries,scene_loader.preparing_scene};
 return field<8?words[field]:~0u;
}

API(publication_reference) u32 publication_reference(u32 field){return field<6?reference_snapshot[field]:~0u;}

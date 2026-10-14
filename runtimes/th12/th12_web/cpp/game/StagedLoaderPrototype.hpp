#pragma once
#include "Types.hpp"
namespace th11::prototype {
enum class Work:u32{Waiting,Ready,Failed};
enum class LoadPhase:u32{Idle,WaitCapture,WaitMinimum,Hud,Scene,Timeline,Ready,Aborted,Failed};
struct StageActions {
 virtual ~StageActions()=default;
 virtual bool retire_owner()=0;
 virtual bool enter_work_and_initialize()=0;
 virtual Work prepare_hud()=0;
 virtual Work prepare_scene()=0;
 virtual bool publish_empty_owner()=0;
 virtual Work prepare_timeline()=0;
};
struct StagedLoader {
 LoadPhase phase=LoadPhase::Idle;
 u64 deadline=0,last_sample=0;
 bool initial_stage=false,has_sample=false;
 bool request(StageActions& actions,bool initial=false){
  if(phase!=LoadPhase::Idle&&phase!=LoadPhase::Ready)return false;
  if(!actions.retire_owner()){phase=LoadPhase::Failed;return false;}
  initial_stage=initial;has_sample=false;deadline=0;phase=LoadPhase::WaitCapture;return true;
 }
 bool pump(StageActions& actions,u64 now,i32 first_capture_index,u32 supervisor_flags){
  if(phase==LoadPhase::Idle||phase==LoadPhase::Ready)return true;
  if(phase==LoadPhase::Aborted||phase==LoadPhase::Failed)return false;
  if(has_sample&&now<last_sample){phase=LoadPhase::Failed;return false;}
  has_sample=true;last_sample=now;
  for(;;){
   if(phase==LoadPhase::WaitCapture){
    if(first_capture_index>=0){
     if(supervisor_flags&0x180){phase=LoadPhase::Aborted;return false;}
     return true;
    }
    const u64 minimum=initial_stage?0:60000000;
    if(now>~u64(0)-minimum){phase=LoadPhase::Failed;return false;}
    deadline=now+minimum;phase=LoadPhase::WaitMinimum;
   }
   if(phase==LoadPhase::WaitMinimum){
    if(now<deadline)return true;
    if(!actions.enter_work_and_initialize()){phase=LoadPhase::Failed;return false;}
    phase=LoadPhase::Hud;
   }
   if(phase==LoadPhase::Hud){
    const auto result=actions.prepare_hud();
    if(result==Work::Waiting)return true;
    if(result==Work::Failed){phase=LoadPhase::Failed;return false;}
    phase=LoadPhase::Scene;
   }
   if(phase==LoadPhase::Scene){
    const auto result=actions.prepare_scene();
    if(result==Work::Waiting)return true;
    if(result==Work::Failed){phase=LoadPhase::Failed;return false;}
    if(!actions.publish_empty_owner()){phase=LoadPhase::Failed;return false;}
    phase=LoadPhase::Timeline;
   }
   if(phase==LoadPhase::Timeline){
    const auto result=actions.prepare_timeline();
    if(result==Work::Waiting)return true;
    if(result==Work::Failed){phase=LoadPhase::Failed;return false;}
    phase=LoadPhase::Ready;return true;
   }
   phase=LoadPhase::Failed;return false;
  }
 }
};
}

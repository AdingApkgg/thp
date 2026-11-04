// Diagnostic schedules only. No original camera values enter this fixture.
#include "H:/code/thp/artifacts/th14/scene-camera-read-job-nov04/session-observer-v2/fixture-source.cpp"
namespace {
struct PerspectiveRepSplit {
 u32 callback=0,ordinal=0,pause=0,start=0,end=0,start_visits=0,end_visits=0;
 u32 started=0,ended=0,waits=0,private_waits=0,prefix_captured=0,captured=0,failed=0;
 u64 first_ns=0,last_ns=0;SceneCamera prefix{},snapshot{};
};
PerspectiveRepSplit perspective_splits[8];bool perspective_splits_installed=false,split_player_installed=false;
void capture_perspective_splits(){
 if(!session.battle)return;
 for(u32 stage=2;stage<=6;++stage){auto& w=perspective_splits[stage];
  if(w.started&&w.ended&&!w.captured&&session.battle->pending_stage==stage&&session.battle->stage_camera_read_job.copied_words()==75){w.snapshot=session.battle->stage_camera_read_job.snapshot();++w.captured;}
 }
}
}
API(observed_perspective_rep_split) u32 observed_perspective_rep_split(u32 stage,u32 callback,u32 ordinal,u32 pause,u32 start,u32 end,u64 first,u64 last){
 if(!session.battle||stage<2||stage>6||!callback||!ordinal||!pause||pause>=75||start>7||end>7||start==end||first>last||first<probe_clock_ns||public_player_observations!=1||perspective_splits[stage].callback)return 0;
 auto& w=perspective_splits[stage];w.callback=callback;w.ordinal=ordinal;w.pause=pause;w.start=start;w.end=end;w.first_ns=first;w.last_ns=last;
 if(!perspective_splits_installed){
  perspective_splits_installed=true;static auto previous_read=session.battle->stage_camera_read_boundary;
  session.battle->stage_camera_read_boundary=[](u32 copied){
   for(u32 stage=2;stage<=6;++stage){auto& w=perspective_splits[stage];
    if(w.started&&!w.ended&&session.battle&&session.battle->pending_stage==stage&&copied>=w.pause){
     if(!w.prefix_captured){w.prefix=session.battle->stage_camera_read_job.snapshot();++w.prefix_captured;}
     ++w.waits;if(session.battle->incoming_scene_owner)++w.private_waits;return prototype::Work::Waiting;
    }
   }
   return previous_read?previous_read(copied):prototype::Work::Ready;
  };
  static auto previous_perspective=session.stage_load_perspective_boundary;
  session.stage_load_perspective_boundary=[](const SceneCamera& camera,u32 point){
   capture_perspective_splits();
   for(u32 stage=2;stage<=6;++stage){auto& w=perspective_splits[stage];
    if(!w.callback||public_player_observations!=w.callback)continue;
    if(point==w.start&&++w.start_visits==w.ordinal){
     if(w.started||!session.battle||session.battle->pending_stage!=stage||probe_clock_ns>w.first_ns)w.failed=1;
     else{probe_clock_ns=w.first_ns;++w.started;}
    }
    if(point==w.end&&++w.end_visits==w.ordinal){
     if(!w.started||w.ended||probe_clock_ns>w.last_ns)w.failed=1;
     else{probe_clock_ns=w.last_ns;++w.ended;}
    }
    if(w.failed)return false;
   }
   return !previous_perspective||previous_perspective(camera,point);
  };
 }
 return 1;
}
API(perspective_rep_split_capture_install) u32 perspective_rep_split_capture_install(){
 if(split_player_installed||!session.battle||public_player_observations!=1)return 0;
 split_player_installed=true;static auto previous_player=session.battle->before_player_update;
 session.battle->before_player_update=[](const GameBattle& battle){capture_perspective_splits();previous_player(battle);};return 1;
}
API(perspective_rep_split_word) u32 perspective_rep_split_word(u32 stage,u32 prefix,u32 word){
 if(stage>=8||word>=75)return ~0u;const auto& w=perspective_splits[stage];
 if(prefix&&!w.prefix_captured||!prefix&&!w.captured)return ~0u;
 return native_camera_word(prefix?w.prefix:w.snapshot,word);
}
API(perspective_rep_split_meta) u32 perspective_rep_split_meta(u32 stage,u32 index){
 if(stage>=8)return ~0u;const auto& w=perspective_splits[stage];
 const u32 values[]={w.callback,w.ordinal,w.pause,w.start,w.end,w.start_visits,w.end_visits,w.started,w.ended,w.waits,w.private_waits,w.prefix_captured,w.captured,w.failed};return index<14?values[index]:~0u;
}

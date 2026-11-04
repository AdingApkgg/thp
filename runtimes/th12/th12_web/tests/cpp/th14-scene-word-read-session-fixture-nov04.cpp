// Relative host schedule and read-only intermediate camera observations.
#include "th14-source-camera-first-rng-read-fixture-nov04.cpp"
namespace {
struct AuxiliaryCameraRead {u32 callback=0,ordinal=0,point=0,visits=0,captured=0;SceneCamera camera;};
AuxiliaryCameraRead auxiliary_reads[8];bool auxiliary_reads_installed=false;
u32 native_camera_word(const SceneCamera& camera,u32 index){
 if(index>=75)return ~0u;const u32 at=index<18?index*4:index<21?offsetof(SceneCamera,target_offset)+(index-18)*4:index==21?offsetof(SceneCamera,fov):index==22?offsetof(SceneCamera,render_width):index==23?offsetof(SceneCamera,render_height):offsetof(SceneCamera,view)+(index-24)*4;
 u32 value;std::memcpy(&value,reinterpret_cast<const u8*>(&camera)+at,4);return value;
}
struct PartialSceneCopy {u32 stage=0,callback=0,start=0,pause=0,end=0,mode=0,started=0,ended=0,suffix=0,waits=0,private_owner=0,captured=0,failed=0,publisher_stage=0;u64 first_ns=0,last_ns=0;SceneCamera snapshot;} partial_scene_copy;
bool partial_player_capture_installed=false;
}
API(observed_auxiliary_camera_read) u32 observed_auxiliary_camera_read(u32 stage,u32 callback,u32 ordinal,u32 point){
 if(stage<2||stage>6||!callback||!ordinal||point<6||point>7||auxiliary_reads[stage].callback||public_player_observations!=1)return 0;
 auto& w=auxiliary_reads[stage];w.callback=callback;w.ordinal=ordinal;w.point=point;
 if(!auxiliary_reads_installed){auxiliary_reads_installed=true;static auto previous=session.stage_load_perspective_boundary;
  session.stage_load_perspective_boundary=[](const SceneCamera& camera,u32 point){
   const auto stage=session.state.stage;if(stage>=2&&stage<=6){auto& w=auxiliary_reads[stage];if(w.callback&&public_player_observations==w.callback&&point==w.point&&++w.visits==w.ordinal){w.camera=camera;++w.captured;}}
   return !previous||previous(camera,point);
  };
 }
 return 1;
}
API(auxiliary_camera_read_word) u32 auxiliary_camera_read_word(u32 stage,u32 word){return stage<8&&auxiliary_reads[stage].captured?native_camera_word(auxiliary_reads[stage].camera,word):~0u;}
API(auxiliary_camera_read_meta) u32 auxiliary_camera_read_meta(u32 stage,u32 index){if(stage>=8)return ~0u;const auto& w=auxiliary_reads[stage];const u32 values[]={w.callback,w.ordinal,w.point,w.visits,w.captured};return index<5?values[index]:~0u;}
API(observed_partial_scene_copy) u32 observed_partial_scene_copy(u32 stage,u32 callback,u32 start,u32 pause,u32 end,u64 first,u64 last,u32 mode){
 auto& w=partial_scene_copy;
 if(!session.battle||w.callback||stage<2||stage>6||!callback||!start||start>=end||end>75||!pause||pause>=75||first>last||first<probe_clock_ns||public_player_observations!=1||mode<1||mode>2)return 0;
 w.stage=stage;w.callback=callback;w.start=start;w.pause=pause;w.end=end;w.first_ns=first;w.last_ns=last;w.mode=mode;
 static auto previous_read=session.battle->stage_camera_read_boundary;
 session.battle->stage_camera_read_boundary=[](u32 copied){
  auto& w=partial_scene_copy;
  if(w.started&&!w.suffix&&w.mode!=2&&copied>=w.pause){++w.waits;if(session.battle->incoming_scene_owner)++w.private_owner;return prototype::Work::Waiting;}
  return previous_read?previous_read(copied):prototype::Work::Ready;
 };
 static auto previous_publish=session.stage_load_camera_word_boundary;
 session.stage_load_camera_word_boundary=[](const Stage& owner,u32 published){
  auto& w=partial_scene_copy;
  if(session.state.stage==w.stage&&public_player_observations==w.callback){
   if(published==w.start){if(w.started||probe_clock_ns>w.first_ns){w.failed=1;return false;}probe_clock_ns=w.first_ns;++w.started;w.publisher_stage=owner.state.stage_number;}
   if(published==w.end){if(!w.started||w.ended||probe_clock_ns>w.last_ns){w.failed=1;return false;}probe_clock_ns=w.last_ns;w.suffix=1;++w.ended;}
  }
  return !previous_publish||previous_publish(owner,published);
 };
 return 1;
}
// Install after observed_worker_events() has attached its Player observer.
API(partial_scene_capture_install) u32 partial_scene_capture_install(){
 if(partial_player_capture_installed||!session.battle||public_player_observations!=1)return 0;
 partial_player_capture_installed=true;static auto previous_player=session.battle->before_player_update;
 session.battle->before_player_update=[](const GameBattle& battle){
  previous_player(battle);auto& w=partial_scene_copy;
  if(w.started&&!w.captured&&session.state.stage==w.stage&&battle.stage_camera_read_job.copied_words()==75){w.snapshot=battle.stage_camera_read_job.snapshot();++w.captured;}
 };
 return 1;
}
API(partial_scene_copy_word) u32 partial_scene_copy_word(u32 word){return partial_scene_copy.captured?native_camera_word(partial_scene_copy.snapshot,word):~0u;}
API(partial_scene_copy_meta) u32 partial_scene_copy_meta(u32 index){const auto& w=partial_scene_copy;const u32 values[]={w.callback,w.start,w.pause,w.end,w.started,w.ended,w.suffix,w.waits,w.private_owner,w.captured,w.failed,w.publisher_stage};return index<12?values[index]:~0u;}
